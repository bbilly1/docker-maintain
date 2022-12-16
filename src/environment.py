"""return regular user environment variables"""

import os


def read_environ():
    """return config dict"""
    username = os.environ.get("SUDO_USER")
    if not username:
        raise ValueError("sudo user not found")

    home = os.path.expanduser(f"~{username}")

    backup_base = os.path.join(home, "backup")
    if not os.path.exists(backup_base):
        raise FileNotFoundError("missing backup_base folder")

    docker_base = os.path.join(home, "docker")
    if not os.path.exists(docker_base):
        raise FileNotFoundError("missing docker_base folder")

    return {
        "home": home,
        "backup_base": backup_base,
        "docker_base": docker_base,
        "uid": int(os.environ.get("SUDO_UID")),
        "gid": int(os.environ.get("SUDO_GID")),
        "username": username,
        "hostname": os.uname().nodename or "host",
    }
