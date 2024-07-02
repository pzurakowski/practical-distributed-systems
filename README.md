## Deployment

1. Log in to first of the hosts.

2. Install ansible
```
sudo add-apt-repository -y ppa:ansible/ansible
sudo apt -y install ansible sshpass
```

3. Clone the repository
```
git clone https://github.com/pzurakowski/practical-distributed-systems
```

4. Run installation playbooks
```
cd practical-distributed-systems/deployment
ansible-playbook --extra-vars "ansible_user=<user> ansible_password=<password> ansible_ssh_extra_args='-o StrictHostKeyChecking=no'" -i hosts kafka.yaml docker.yaml haproxy.yaml aerospike.yaml worker.yaml front.yaml
```