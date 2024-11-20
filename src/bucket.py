"""upload to s3 bucket"""

from os import chown
from pathlib import Path
import boto3


class S3Handler:
    """interact with s3 bucket"""

    def __init__(self, config):
        self.config = config

    def is_active(self) -> bool:
        """check if integration is active"""
        return all(
            (
                self.config.get("aws_access_key_id"),
                self.config.get("aws_secret_access_key"),
                self.config.get("bucket_name"),
            )
        )

    def process(self, archive_path):
        """process bucket sync"""
        if not self.is_active():
            print("s3 integration not active")
            return

        self.upload_file(Path(archive_path))
        if self.config.get("rotate_s3"):
            items_to_keep = int(self.config["rotate_s3"])
            self.rotate_bucket(items_to_keep)

    def upload_file(self, file_path: Path):
        """upload file to bucket"""
        print(f"upload {file_path.name} to s3 bucket")
        bucket = self.get_bucket()
        bucket.upload_file(file_path, file_path.name)

    def get_resource(self):
        """get resource object"""
        session = boto3.Session(
            aws_access_key_id=self.config["aws_access_key_id"],
            aws_secret_access_key=self.config["aws_secret_access_key"],
        )
        s3_resource = session.resource("s3", endpoint_url=self.config.get("endpoint_url"))
        return s3_resource

    def get_bucket(self):
        """get bucket"""
        s3_resource = self.get_resource()
        bucket = s3_resource.Bucket(self.config["bucket_name"])
        return bucket

    def rotate_bucket(self, items_to_keep: int) -> None:
        """rotate files in bucket"""
        sorted_bucket_items = self.get_bucket_objects()
        objects_to_delete = list(sorted_bucket_items[items_to_keep:])
        if objects_to_delete:
            delete_keys = [{"Key": obj.key} for obj in objects_to_delete]
            try:
                s3_resource = self.get_resource()
                response = s3_resource.meta.client.delete_objects(
                    Bucket=self.config["bucket_name"],
                    Delete={"Objects": delete_keys}
                )
                print("Deleted:", response["Deleted"])
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"Error deleting objects: {e}")
        else:
            print("No objects to delete.")

    def get_bucket_objects(self):
        """get available backups from bucket"""
        bucket = self.get_bucket()
        bucket_items = list(bucket.objects.filter(Prefix=f'docker_{self.config["hostname"]}'))
        sorted_bucket_items = sorted(bucket_items, key=lambda obj: obj.last_modified, reverse=True)

        return sorted_bucket_items

    def download_object(self, backup_file):
        """download remote backup file to local folder"""
        print(f"Download backup file: {backup_file}")
        bucket = self.get_bucket()
        target_path = Path(self.config["backup_base"]) / backup_file
        bucket.download_file(backup_file, target_path)
        chown(target_path, self.config["uid"], self.config["gid"])
