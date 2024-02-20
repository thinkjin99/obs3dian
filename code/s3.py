import boto3
import json
import pathlib
from urllib import parse


class S3:
    def __init__(self, profile_name: str, bucket_name: str) -> None:
        self.session = boto3.Session(profile_name=profile_name)
        self.s3 = self.session.client("s3")
        self.bucket_name = bucket_name
        return

    def create_bucket(self):
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
        return

    def put_public_access_policy(self):
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
        self.s3.put_bucket_policy(Bucket=self.bucket_name, Policy=json.dumps(policy))
        return

    def create_key(self, markdown_file_name: str, image_name: str):
        return f"{markdown_file_name}/{image_name}"

    def put_image(self, key: str, file_path: pathlib.Path) -> None:
        self.s3.put_object(
            Bucket=self.bucket_name,
            Body=file_path.open("rb"),
            Key=key,
        )
        return

    def create_s3_url(self, object_key: str) -> str:
        region = self.session.region_name
        s3_url = f"https://{self.bucket_name}.s3.{region}.amazonaws.com/{parse.quote(object_key)}"
        return s3_url


# bucket_name = "obs3dian"
# s3 = S3("default", bucket_name)
# print(s3.create_s3_link("test2.md/Pasted image 20231227161358.png"))
