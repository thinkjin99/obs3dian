import boto3
from botocore.exceptions import ClientError
import json
from pathlib import Path
from urllib import parse

from .markdown import ImageText


class S3:
    """
    Class to control S3
    this class can make bucket, set public access, put images in s3.
    To use this class you need AWS CLI profile which has permission to create public bucket and put images.
    """

    def __init__(
        self,
        bucket_name: str,
        profile_name: str | None = None,
        aws_access_key: str | None = None,
        aws_secret_key: str | None = None,
    ) -> None:

        if profile_name:
            self.session = boto3.Session(profile_name=profile_name)
        elif aws_access_key and aws_secret_key:
            self.session = boto3.Session(
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name="ap-northeast-2",
            )
        else:
            raise ValueError("Need profile name or Access Key & Secret Key")

        self.s3 = self.session.client("s3")
        self.bucket_name = bucket_name
        return

    def _check_bucket_exist(self) -> bool:
        try:
            self.s3.head_bucket(Bucket=self.bucket_name)  # check bucket is exists
            return True

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":  # if bucket not exists return false
                return False
            elif error_code == "403":  # 403 means bucket exists but no permission
                return True
            else:  # bad reqeust
                raise e

    def _put_public_access_policy(self) -> None:
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
            )  # put bucket public access

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
            self._put_public_access_policy()
            return True

        except ClientError as e:
            print("Error occured in create bucket")
            raise e

    def _get_image_url(self, markdown_path: Path, image_path: Path) -> str:
        region = self.session.region_name
        key = f"{markdown_path.stem} / {image_path.name}"
        s3_url = f"https://{self.bucket_name}.s3.{region}.amazonaws.com/{parse.quote(key)}"  # image uploaded url
        return s3_url

    def put_image(self, markdown_path: Path, image: ImageText) -> ImageText:
        try:
            self.s3.put_object(
                Bucket=self.bucket_name,
                Body=image.path.open("rb"),
                Key=f"{markdown_path.stem} / {image.name}",
                ContentType=f"image/{image.path.suffix}",
            )  # upload image
            s3_url = self._get_image_url(markdown_path, image.path)
            image.s3_url = s3_url
            return image

        except ClientError as e:
            print(f"Error Occured in uploading {image.path}")
            raise e
