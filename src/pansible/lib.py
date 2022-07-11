import json
import logging

from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.playbook.play import Play
from ansible.plugins.callback import CallbackBase
from ansible.plugins.loader import module_loader
from ansible import context
from ansible.module_utils.common.collections import ImmutableDict

try:
    from ansible.executor import task_result
    task_result._IGNORE = ('skipped', )
except Exception as e:
    logging.error("Hack for https://github.com/ansible/pytest-ansible/issues/47 failed: {}".format(repr(e)))

# class Singleton(type):

#     _instances = {}
#     _lock = Lock()

#     def __call__(cls, *args, **kwargs):
#         with cls._lock:
#             if cls not in cls._instances:
#                 instance = super(Singleton, cls).__call__(*args, **kwargs)
#                 cls._instances[cls] = instance
#         return cls._instances[cls]


# class TQM(with_metaclass(Singleton, object)):
#     """Singleton class

#     """
#     def __init__(self):
#         self.tqm = TaskQueueManager()


class ResultsCollectorJSONCallback(CallbackBase):

    def __init__(self, *args, **kwargs):
        super(ResultsCollectorJSONCallback, self).__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}

    def v2_runner_on_unreachable(self, result):
        host = result._host
        self.host_unreachable[host.get_name()] = result._result

    def v2_runner_on_ok(self, result, *args, **kwargs):
        """Print a json representation of the result.

        Also, store the result in an instance attribute for retrieval later
        """
        host = result._host
        self.host_ok[host.get_name()] = result._result

    def v2_runner_on_failed(self, result, *args, **kwargs):
        host = result._host
        self.host_failed[host.get_name()] = result._result

    @property
    def results(self):
        return {"contacted": self.host_ok, "unreachable": self.host_unreachable, "failed": self.host_failed}


class ModuleDispatcher(object):
    def __init__(self, hosts, vm, loader, tqm):
        self.tqm = tqm
        self.hosts = hosts
        self.vm = vm
        self.loader = loader

    def __getattr__(self, attr):
        if not module_loader.has_plugin(attr):
            raise Exception("Unsupported ansible module \"{}\"".format(attr))
        self.module_name = attr
        return self._run

    def _run(self, *args, **kwargs):
        if args:
            kwargs.update(dict(_raw_params=' '.join(args)))

        verbosity = kwargs.pop("verbosity", 0)
        context.CLIARGS = ImmutableDict(verbosity=verbosity)

        play_source = dict(
            name="pansible",
            hosts=self.hosts,
            become=kwargs.pop("become", False),
            become_user=kwargs.pop("become_user", None),
            gather_facts='no',
            tasks=[
                dict(action=dict(module=self.module_name, args=kwargs)),
            ]
        )
        play = Play().load(
            play_source,
            variable_manager=self.vm,
            loader=self.loader
        )
        try:
            self.tqm.run(play)
            return self.tqm._stdout_callback
        finally:
            if self.tqm:
                self.tqm.cleanup()
            if self.loader:
                self.loader.cleanup_all_tmp_files()


class AnsibleHosts(object):

    def __init__(self, inventory, hosts=[]):
        self.inventory = inventory
        self.hosts = hosts

        self.loader = DataLoader()

        self.im = InventoryManager(loader=self.loader, sources=self.inventory)
        self.vm = VariableManager(loader=self.loader, inventory=self.im)

        self.tqm = TaskQueueManager(
            inventory=self.im,
            variable_manager=self.vm,
            loader=self.loader,
            passwords=dict(conn_pass=None, become_pass=None, vault_pass=None),
            stdout_callback=ResultsCollectorJSONCallback()
        )

    @property
    def ansible(self):
        return ModuleDispatcher(self.hosts, self.vm, self.loader, self.tqm)


def main():
    local = AnsibleHosts("../../ansible/inv.yaml", hosts=["localhost"])
    res = local.ansible.shell("notexist", verbosity=3)
    print("Result: " + json.dumps(res.results, indent=4))


if __name__ == "__main__":
    main()
