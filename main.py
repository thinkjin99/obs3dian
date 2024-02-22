import json
import typer
from pathlib import Path

from src.core import create_obs3dian_runner
from src.s3 import S3

APP_NAME = "obs3dian"
SETUP_FILE_NAME = "credentials.json"
APP_DIR_PATH = typer.get_app_dir(APP_NAME)
app = typer.Typer(name=APP_NAME)


def load_credentials() -> dict:
    config_path = Path(APP_DIR_PATH) / SETUP_FILE_NAME
    with config_path.open("r") as f:
        credentials = json.load(f)
    return credentials


def conver_path_absoulte(path: Path):
    path = path.expanduser()
    return path.resolve()


@app.command()
def init():
    credentials: dict = load_credentials()
    output_folder_path = conver_path_absoulte(Path(credentials["output_folder_path"]))

    s3 = S3(credentials["profile_name"], credentials["bucket_name"])
    print("Connected to AWS S3")

    if s3.create_bucket():
        print("Bucket already exists...")

    s3.put_public_access_policy()

    if not output_folder_path.exists():
        output_folder_path.mkdir()
        print(f"Output Folder is made in {output_folder_path.name}")
    else:
        print("Output Folder is already exists (run config to change)")
    return True


@app.command()
def config():
    profile_name = input("AWS Profile Name: ")
    bucket_name = input("S3 bucket Name: ")
    output_path = input("Output Path: ")
    json_data = {
        "profile_name": profile_name,
        "bucket_name": bucket_name,
        "output_folder_path": output_path,
    }

    app_dir_path = Path(APP_DIR_PATH)
    if not app_dir_path.exists():
        app_dir_path.mkdir()

    config_path = app_dir_path / SETUP_FILE_NAME
    with config_path.open("w") as f:
        json.dump(json_data, f)


@app.command()
def run(user_input_path: Path):
    user_input_path = conver_path_absoulte(user_input_path)
    credentials: dict = load_credentials()
    output_folder_path = conver_path_absoulte(Path(credentials["output_folder_path"]))
    s3 = S3(credentials["profile_name"], credentials["bucket_name"])

    runner = create_obs3dian_runner(s3, output_folder_path)

    if user_input_path.is_dir():
        file_paths = [
            file_path for file_path in user_input_path.rglob("*.md")
        ]  # 마크다운 파일 전체 적용
    else:
        file_paths = [user_input_path]
    import time

    with typer.progressbar(
        label="Processing", iterable=file_paths, show_eta=False
    ) as progeress:

        for file_path in progeress:
            typer.echo(f"\t\t{file_path.name[:20]:<20}", nl=False)
            time.sleep(1)

        # progeress.update(0)

        # runner(file_path)


if __name__ == "__main__":
    app()
    # load_credentials()
    # config()
