# Docker Maintain
Collection of maintenance scripts for my docker VPS servers.

## Core functionality
- Easy volume snapshots for Docker container.
- Dump *mariadb* and *postgres* databases to sql files.
- Pack it all up into a compressed tar.gz file for further archiving.

## Command line arguents
- **update**: Update all containers
- **snapshot**: Create snapshot of volumes and database containers

## Run
Use sudo from your regular user, not as root, e.g.:
```bash
sudo python maintain.py snapshot
sudo python maintain.py update
```

## Expected folder structure
This script expect the following folder structure:
```
$HOME/docker                        <-- base folder
$HOME/docker/docker-compose.yml     <-- your docker compose file
$HOME/docker/<any volume folder>    <-- all volume mount folder
$HOME/backup                        <-- backup base folder
```

Ideal companion to the **Docker Ubuntu** playbook from my [Ansible Playbooks](https://github.com/bbilly1/ansible-playbooks) collection.
