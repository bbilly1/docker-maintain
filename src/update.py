"""update docker containers"""

import subprocess

from src.snapper import DockerCompose


class Containers:
    """interact with containers"""

    def __init__(self, config):
        self.compose = DockerCompose(config).compose_file
        self.command_base = ["docker", "compose", "-f", self.compose]

    def update(self):
        """update"""
        self._pull_updates()
        self._down_containers()
        self._restart_containers()

    def _pull_updates(self):
        """pull containers with updates"""
        command = self.command_base + ["pull"]
        subprocess.run(command, check=True)

    def _down_containers(self):
        """take all containers down"""
        command = self.command_base + ["down", "--remove-orphans"]
        subprocess.run(command, check=True)

    def _restart_containers(self):
        """restart containers with new images"""
        command = self.command_base + ["up", "-d"]
        subprocess.run(command, check=True)
