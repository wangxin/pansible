# pansible
A wrapper for calling ansible modules on remote hosts using python in an intuitive way.

This project was inspired by the pytest-ansible plugin. Ansible is a great tool to perform various operations on remote hosts. However, there are some pain points using the ansible playbook.

* It is hard to figure out where a variable got defined. And it is not easy to know the scope of variables.
* Ansible playbook supports conditions, blocks, loops, includes and roles. These features are nice. However, comparing with a real programming language, these features are not powerful and flexible enough.
* It is difficult to manipulate data like dict and list in ansible playbook.

Despite the playbook pain points, ansible has huge amount of modules that can perform various operations on remote hosts. What's more, ansible only needs SSH access to remote hosts. No client (except python) is required on remote hosts.

The idea of this project is to have an intuitive way of calling the ansible modules on remote hosts using python instead of playbook. Then we can have all the sweet points of ansible modules and SSH access, meanwhile we can avoid the pain points of playbooks by using a real programming language.

The target is to create some classes to represent remote hosts. Then, we can create instances of the classes to interact with remote hosts, and call various ansible modules on remote hosts, using python.

Dependency of this tool will be just inventory files, optional host_vars and group_vars. Comparing with pure ansible, this tool is to replace playbooks with python scripts.

# Development

1. Clone the code.

2. Setup python virtual environment.
Under repository root folder:

```
python -m venv .venv
source activate.sh
pip install --upgrade pip
pip install -r src/requirements.txt
pip install -r src/requirements-dev.txt
pre-commit install    # Install pre-commit hooks
```
