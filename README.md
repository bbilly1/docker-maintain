# Docker Maintain
Collection of maintenance scripts for my docker VPS servers.

## Core functionality
- Easy volume snapshots for Docker container.
- Dump *mariadb* and *postgres* databases to sql files.
- Pack it all up into a compressed tar.gz file for further archiving.
- Optionally sync the archive file to a S3 bucket
- Optionally rotate backup files

## Command line arguents
- **update**: Update all containers
- **snapshot**: Create snapshot of volumes and database containers
- **restore**: Restore a local or S3 backup file

## Config
You can configure the behaviour by creating a `.env` file in the root of this project. Take a look at the `.sample.env` file for an overview. Supported variables:

- `AWS_ACCESS_KEY_ID`: Optional, for S3 backup
- `AWS_SECRET_ACCESS_KEY`: Optional, for S3 backup
- `BUCKET_NAME`: Optional, for S3 backup
- `ENDPOINT_URL`: Optional, for S3 backup
- `ROTATE_S3`: Optional, when using S3 backup, configure how many backup objects to keep
- `ROTATE_LOCAL`: Optional, configure how many local tar.gz backup files to keep
  - Outdated backups are trashed with `trash-cli`, you'll have to empty the trash yourself.

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

## Dev Setup

```
python -m venv .venv
source .venv/bin/activate
pre-commit install
```
