"""restore backup"""

import tarfile
from pathlib import Path

from src.bucket import S3Handler
from src.snapper import Backup


class Restore:
    """handle restore functionality"""

    def __init__(self, config):
        self.config = config

    def process(self):
        """entry point, restore backup"""
        available_backups = self.get_backups()
        selected_backup_file = self.select_backup(available_backups)
        self.download_backup(selected_backup_file)
        self.restore(selected_backup_file)

    def restore(self, selected_backup_file):
        """restore file"""
        tar_gz_path = Path(self.config["backup_base"]) / selected_backup_file
        extract_to = Path(self.config["docker_base"])
        with tarfile.open(tar_gz_path, "r:gz") as tar:
            tar.extractall(path=extract_to)

    def get_backups(self):
        """get available backups"""
        backups = set()
        backups.update(self._get_local_backups())
        backups.update(self._get_s3_backups())

        if not backups:
            raise FileNotFoundError("did not find any available backups")

        available_backups = sorted(list(backups), reverse=True)
        return available_backups

    def _get_local_backups(self):
        """get local backups"""
        return set(Backup({}, self.config).get_available_backups())

    def _get_s3_backups(self):
        """get s3 objects"""
        handler = S3Handler(self.config)
        if not handler.is_active():
            return {}

        s3_backups = {i.key for i in handler.get_bucket_objects()}

        return s3_backups

    def select_backup(self, available_backups):
        """select backup"""
        for idx, backup in enumerate(available_backups):
            print(f"[{idx}] {backup}")

        to_restore = input("pick idx of backup to restore: ")
        if not to_restore.isdigit():
            raise ValueError("expected int")

        selected_backup_file = available_backups[to_restore]
        return selected_backup_file

    def download_backup(self, selected_backup_file):
        """download backup file if needed"""
        local_files = self._get_local_backups()
        if selected_backup_file in local_files:
            print("restore from local file")
            return

        S3Handler(self.config).download_object(selected_backup_file)
