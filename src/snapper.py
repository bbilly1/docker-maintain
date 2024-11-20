"""make snapshots"""

import gzip
import os
import re
import shutil
import subprocess
import tarfile
from datetime import datetime

import yaml

from src.bucket import S3Handler


class DockerCompose:
    """handle docker compose file"""

    NAME = "docker-compose.yml"

    def __init__(self, config):
        self.config = config
        self.compose_file = self.find_path()

    def find_path(self):
        """find path on filesystem"""
        docker_base = self.config["docker_base"]
        file_path = os.path.join(docker_base, self.NAME)
        print(file_path)
        if not os.path.exists(file_path):
            raise ValueError("docker-compose file not found")

        return file_path

    def read_docker_compose(self):
        """read compose file"""
        with open(self.compose_file, "r", encoding="utf-8") as file:
            compose = yaml.safe_load(file)

        return compose


class Backup:
    """handle backups for mariadb and postgres"""

    def __init__(self, compose, config):
        self.services = compose.get("services")
        self.config = config
        self.file_path = self.build_tar_path()
        self.exec_base = False

    def build_tar_path(self):
        """build tar archive path"""
        host_name = self.config["hostname"]
        now = datetime.now().strftime("%Y%m%d")
        file_name = f"docker_{host_name}_{now}.tar"
        file_path = os.path.join(self.config["backup_base"], file_name)
        return file_path

    def backup_folder(self):
        """backup base folder"""
        docker_base = self.config["docker_base"]
        print(f"snapshot {docker_base} to {self.file_path}")
        with tarfile.open(self.file_path, "w") as tar:
            tar.add(docker_base, arcname=os.path.basename(docker_base))

        os.chown(self.file_path, self.config["uid"], self.config["gid"])

    def backup_database(self):
        """backup all databases"""
        if not self.services:
            raise ValueError("no services defined in compose")

        for service_name, service_conf in self.services.items():
            image = service_conf.get("image")
            if not image:
                continue

            self.exec_base = ["docker", "exec", "-it", service_name]
            if image.startswith("mariadb"):
                print(f"{service_name}: backup mariadb container")
                self.backup_maria(service_name)
            elif image.startswith("postgres"):
                print(f"{service_name}: backup postgres container")
                self.backup_postgres(service_name)

    def backup_maria(self, service_name):
        """make backup of mariadb"""
        root_pw = self._get_maria_root_pw()
        self._dump_maria_db(root_pw, service_name)

    def _get_maria_root_pw(self):
        """get root pw from env var"""
        args = self.exec_base + ["bash", "-c", 'echo "$MYSQL_ROOT_PASSWORD"']
        root_pw_raw = subprocess.run(args, capture_output=True, check=True)
        root_pw = root_pw_raw.stdout.decode().strip()

        return root_pw

    def _dump_maria_db(self, root_pw, service_name):
        """write db to file"""
        backup_base = self.config["backup_base"]
        file_path = os.path.join(backup_base, f"{service_name}.sql")

        args = self.exec_base + ["mariadb-dump", "-u", "root", f"-p{root_pw}", "--all-databases"]
        with open(file_path, "w", encoding="utf-8") as outfile:
            subprocess.run(args, stdout=outfile, check=True)

        with tarfile.open(self.file_path, "a") as tar:
            tar.add(file_path, arcname=f"{service_name}.sql")

        os.remove(file_path)

    def backup_postgres(self, service_name):
        """make backup of postgresql db"""
        user = self._get_pg_user()
        self._dump_pg_db(user, service_name)

    def _get_pg_user(self):
        """get username for postgresql db"""
        args = self.exec_base + ["bash", "-c", 'echo "$POSTGRES_USER"']
        user_raw = subprocess.run(args, capture_output=True, check=True)
        user = user_raw.stdout.decode().strip()

        return user

    def _dump_pg_db(self, user, service_name):
        """dump to file"""
        backup_base = self.config["backup_base"]
        file_path = os.path.join(backup_base, f"{service_name}.sql")
        args = self.exec_base + ["pg_dump", "-U", user]
        with open(file_path, "w", encoding="utf-8") as outfile:
            subprocess.run(args, stdout=outfile, check=True)

        with tarfile.open(self.file_path, "a") as tar:
            tar.add(file_path, arcname=f"{service_name}.sql")

        os.remove(file_path)

    def compress(self):
        """compress final result"""
        print(f"compress: {self.file_path}")
        new_path = self.file_path + ".gz"
        with open(self.file_path, "rb") as f_in:
            with gzip.open(new_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        os.remove(self.file_path)
        return new_path

    def get_available_backups(self):
        """get available backup files"""
        host_name = self.config["hostname"]
        pattern = f"docker_{host_name}_" + r"[0-9]{8}.tar.gz"
        backups = [i for i in os.listdir(self.config["backup_base"]) if re.match(pattern, i)]
        sorted_all_files = sorted(backups, reverse=True)

        return sorted_all_files

    def rotate(self, items_to_keep: int) -> None:
        """rotate local backups"""
        sorted_all_files = self.get_available_backups()
        backups_to_delete = list(sorted_all_files[items_to_keep:])
        for backup_file in backups_to_delete:
            backup_file_path = os.path.join(self.config["backup_base"], backup_file)
            os.remove(backup_file_path)
            print(f"Deleted: {backup_file}")


def take_snapshot(config):
    """entry point"""
    compose = DockerCompose(config).read_docker_compose()
    backup = Backup(compose, config=config)
    backup.backup_folder()
    backup.backup_database()
    archive_path = backup.compress()

    S3Handler(config).process(archive_path)

    if config.get("rotate_local"):
        items_to_keep = int(config["rotate_local"])
        backup.rotate(items_to_keep)

    return archive_path
