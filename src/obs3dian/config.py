from dataclasses import dataclass
import json
from pathlib import Path
import typer

APP_NAME = "obs3dian"
SETUP_FILE_NAME = "config.json"
APP_DIR_PATH = typer.get_app_dir(APP_NAME)


@dataclass(frozen=True)
class Configuration:
    profile_name: str = ""
    aws_access_key: str = ""
    aws_secret_key: str = ""
    bucket_name: str = "obs3dian"
    output_folder_path: str = "./output"
    image_folder_path: str = "./images"


def load_configs() -> Configuration:
    """
    Load config json file from app dir

    Returns:
        dict: config json
    """

    try:
        config_path = Path(APP_DIR_PATH) / SETUP_FILE_NAME
        with config_path.open("r") as f:
            configs = json.load(f)
        return Configuration(**configs)  # create config data class

    except FileNotFoundError as e:
        print("Config file is not founded... input your configuration\n")


def save_config(json_data: dict):
    app_dir_path = Path(APP_DIR_PATH)  # create app setting folder
    if not app_dir_path.exists():
        app_dir_path.mkdir()

    config_path = app_dir_path / SETUP_FILE_NAME
    with config_path.open("w") as f:
        json.dump(json_data, f)  # write config.json


def remove_config():
    app_dir_path = Path(APP_DIR_PATH)  # create app setting folder
    config_path = app_dir_path / SETUP_FILE_NAME
    try:
        config_path.unlink()
    except FileNotFoundError:
        print("Config file is not exists run config first")
