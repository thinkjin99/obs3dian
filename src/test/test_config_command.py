from unittest.mock import patch

from obs3dian.config import Configuration
from obs3dian.main import config


def test_selecting_profile_clears_stored_access_keys():
    existing = Configuration(
        aws_access_key="old-access",
        aws_secret_key="old-secret",
        bucket_name="bucket",
        output_folder_path="/tmp",
        image_folder_path="/tmp",
    )
    answers = iter(["Y", "obs3dian-uploader", "", "", ""])

    with (
        patch("obs3dian.main.load_configs", return_value=existing),
        patch("builtins.input", side_effect=lambda _: next(answers)),
        patch("obs3dian.main.save_config") as save_config,
    ):
        config()

    saved = save_config.call_args.args[0]
    assert saved["profile_name"] == "obs3dian-uploader"
    assert saved["aws_access_key"] == ""
    assert saved["aws_secret_key"] == ""
