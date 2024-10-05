"""entry point"""

import sys

from dotenv import load_dotenv

load_dotenv()

from src.bucket import S3Handler
from src.environment import read_environ
from src.update import Containers
from src.snapper import take_snapshot


TITLE = """\n================ DOCKER MAINTAIN ================"""
HELP = "valid arguments are update | snapshot | help"

def print_environ(config):
    """pritty print environment"""
    print(TITLE)
    print(f"""
    paths:
      - home: {config.get('home')}
      - docker: {config.get('docker_base')}
      - backup: {config.get('backup_base')}
    user:
      {config.get('username')} ({config.get('uid')}/{config.get('gid')}) on host [{config.get('hostname')}]
    """)
    if config.get("bucket_name"):
        print(f"""
    bucket:
        - {config.get('bucket_name')}
    """)


def main():
    """main function"""
    try:
        arg = sys.argv[1]
    except IndexError:
        print(HELP)
        return

    config = read_environ()
    print_environ(config)
    if arg == "update":
        Containers(config=config).update()
    elif arg == "snapshot":
        archive_path = take_snapshot(config=config)
        S3Handler(config).process(archive_path)
    else:
        print(HELP)


if __name__ == "__main__":
    main()
