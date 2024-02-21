from pathlib import Path

from code.s3 import S3



def set_bucket_config(s3: S3):
    s3.create_bucket()
    s3.put_public_access_policy()
    return


def create_output_folder(output_folder_name: str):
    cwd = Path.cwd()
    output_folder = Path(cwd, output_folder_name)
    if not output_folder.exists():
        output_folder.mkdir()
    return


def set_init_setting(profile_name: str, bucket_name: str, output_folder_name: str):
    s3 = S3(profile_name, bucket_name)
    set_bucket_config(s3)
    create_output_folder(output_folder_name)
    return s3


# create_output_folder("output")
