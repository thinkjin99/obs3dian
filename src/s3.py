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
            assert error_code == "404", "Forbidden or Badrequest on S3"
            return False

    def create_bucket(self) -> bool:
        if self._check_bucket_exist():
            return False
        try:
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
            print("Error occured in create bucket ", e)
            raise e

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
            print("Can't allow public acess to bucket check permission")
            raise e

    def get_s3_url(self, key: str) -> str:
        region = self.session.region_name
        s3_url = (
            f"https://{self.bucket_name}.s3.{region}.amazonaws.com/{parse.quote(key)}"
        )
        return s3_url

    def put_image(self, file_path: Path, key: str) -> Path | None:
        try:
            self.s3.put_object(
                Bucket=self.bucket_name,
                Body=file_path.open("rb"),
                Key=key,
            )
            return file_path

        except ClientError as e:
            print("Error Occured in uploading...\n", e)
