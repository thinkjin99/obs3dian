import boto3
from botocore.exceptions import ClientError
import json
from pathlib import Path
from urllib import parse


class S3:
    def __init__(self, profile_name: str, bucket_name: str) -> None:
        try:
            self.session = boto3.Session(profile_name=profile_name)
            self.s3 = self.session.client("s3")
            self.bucket_name = bucket_name
            return

        except ClientError as e:
            print("Can't Connect S3")
            raise e

    def _check_bucket_exist(self) -> bool:
        try:
            self.s3.head_bucket(Bucket=self.bucket_name)
            return True

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code != "404":  # if no permission or bad request raise error
                raise e
            return False

    def put_public_access_policy(self) -> None:
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "id-1",
                    "Action": ["s3:GetObject"],
                    "Effect": "Allow",
                    "Resource": f"arn:aws:s3:::{self.bucket_name}/*",
                    "Principal": "*",
                }
            ],
        }
        try:
            self.s3.put_bucket_policy(
                Bucket=self.bucket_name, Policy=json.dumps(policy)
            )

        except Exception as e:
            print("Can't allow public acess to bucket")
            raise e

    def create_bucket(self) -> bool:
        try:
            if self._check_bucket_exist():  # If bucket already exists
                return False

            bucket_name = self.bucket_name
            self.s3.create_bucket(
                CreateBucketConfiguration={"LocationConstraint": "ap-northeast-2"},
                Bucket=bucket_name,
                ObjectOwnership="ObjectWriter",
            )

            self.s3.put_public_access_block(
                Bucket=bucket_name,
                PublicAccessBlockConfiguration={
                    "BlockPublicAcls": False,
                    "IgnorePublicAcls": False,
                    "BlockPublicPolicy": False,
                    "RestrictPublicBuckets": False,
                },
            )
            return True

        except ClientError as e:
            print("Error occured in create bucket")
            raise e

    # def create_s3_key(self, markdown_file_name: str, image_name: str) -> str:
    #     """
    #     Create key by makrdown file name and image name.

    #     Args:
    #         markdown_file_name (str): mark down file name
    #         image_name (str): image file name in markdown

    #     Returns:
    #         str: S3 key
    #     """
    #     return f"{markdown_file_name}/{image_name}"

    def get_image_url(self, markdown_path: Path, image_path: Path) -> str:
        region = self.session.region_name
        key = markdown_path / image_path
        s3_url = f"https://{self.bucket_name}.s3.{region}.amazonaws.com/{parse.quote(str(key))}"
        return s3_url

    def put_image(self, markdown_path: Path, image_path: Path) -> Path:
        try:
            self.s3.put_object(
                Bucket=self.bucket_name,
                Body=image_path.open("rb"),
                Key=str(markdown_path / image_path),
            )
            return image_path

        except ClientError as e:
            print(f"Error Occured in uploading {image_path}")
            raise e
