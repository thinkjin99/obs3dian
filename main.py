import concurrent.futures as concurrent_futures
import json
import typer
from pathlib import Path
import time

from src.core import create_obs3dian_runner
from src.s3 import S3

APP_NAME = "obs3dian"
SETUP_FILE_NAME = "config.json"
APP_DIR_PATH = typer.get_app_dir(APP_NAME)

app = typer.Typer(name=APP_NAME)


def _load_configs() -> dict:
    """
    Load config json file from app dir

    Returns:
        dict: config json
    """
    try:
        config_path = Path(APP_DIR_PATH) / SETUP_FILE_NAME
        with config_path.open("r") as f:
            configs = json.load(f)
        return configs

    except FileNotFoundError as e:
        print("Config file is not founded. Run 'obs3dian config' to make config file")
        raise e


def _convert_path_absoulte(path: Path, strict=True) -> Path:
    """

    Resolve path with ~ / ../ and convert it to absolute path

    Args:
        path (Path): path

    Returns:
        Path: Absolute path
    """
    try:
        resolved_path = path.expanduser().resolve(strict=strict)
        return resolved_path

    except OSError as e:
        print("Path is invalid ", e)
        raise e


def _render_animation(future: concurrent_futures.Future, echo_text: str) -> None:
    """
    Rendering loading animation

    Args:
        future (concurrent_futures.Future): future to wait
        description (str): description text to echo in terminal
    """
    i = 0
    animation = ["|", "/", "--", "\\"]
    while not future.done():  # run until uploading is done
        typer.echo(
            f"\r{animation[i % 4]:<2} {echo_text[:20]:<20}", nl=False
        )  # render animation like => | abc.md -> / abc.md -> -- abc.md
        time.sleep(0.2)  # give delay to show animation
        i += 1
    return


@app.command()
def apply():
    """
    Apply settings from .json file
    create bucket and create folder

    Raises:
        e: invalid output path
    """
    configs: dict = _load_configs()
    output_folder_path = _convert_path_absoulte(
        Path(configs["output_folder_path"]), strict=False
    )

    s3 = S3(configs["profile_name"], configs["bucket_name"])
    print("Connected to AWS S3")

    if s3.create_bucket():
        print("Bucket already exists...")

    if configs["is_bucket_public"]:
        s3.put_public_access_policy()

    if not output_folder_path.exists():
        try:
            output_folder_path.mkdir()
            print(f"Create Output Folder in {output_folder_path.name}")

        except OSError as e:
            print(f"Output path {output_folder_path} is invalid")
            raise e
    else:
        print("Output Folder is already exists (Can modify by run obs3dian config)")


@app.command()
def config():
    """
    Write config data to .json file
    """
    profile_name = input("AWS Profile Name: ")
    bucket_name = input("S3 bucket Name: ")
    is_bucket_public = input("Is bucket public? (Y/N): ")
    assert is_bucket_public in ["Y", "y", "N", "n"], "Invalid input press y/n"
    output_path = input("Output Path: ")

    json_data = {
        "profile_name": profile_name,
        "bucket_name": bucket_name,
        "is_bucket_public": is_bucket_public,
        "output_folder_path": output_path,
    }

    app_dir_path = Path(APP_DIR_PATH)  # create app setting folder
    if not app_dir_path.exists():
        app_dir_path.mkdir()

    config_path = app_dir_path / SETUP_FILE_NAME
    with config_path.open("w") as f:
        json.dump(json_data, f)  # write config.json


@app.command()
def run(user_input_path: Path):
    """
    Run obs3dian main command, get image local file paths from md file.
    After extracting image paths upload images to s3 and replace all file links in .md to S3 links.
    Output.md will be wrriten under output folder and it's image links would have been replaced to S3 links

    Args:
        user_input_path (Path): user input path
    """

    user_input_path = _convert_path_absoulte(user_input_path)
    configs: dict = _load_configs()
    output_folder_path = _convert_path_absoulte(Path(configs["output_folder_path"]))
    s3 = S3(configs["profile_name"], configs["bucket_name"])

    runner = create_obs3dian_runner(s3, output_folder_path)  # create main function

    if user_input_path.is_dir():
        markdown_file_paths = [
            file_path for file_path in user_input_path.rglob("**/*.md")
        ]  # get all .md file under input dir
    else:
        markdown_file_paths = [user_input_path]

    assert len(
        markdown_file_paths
    ), f"No md files in {user_input_path}"  # raise error when no md file in input path

    with concurrent_futures.ThreadPoolExecutor(
        max_workers=1
    ) as executor:  # thread for aniamtion
        with typer.progressbar(
            label="Processing", iterable=markdown_file_paths, show_eta=False
        ) as progeress:  # typer progress bar
            for markdown_file_path in progeress:
                # print progress bar
                typer.echo("")  # new line
                future = executor.submit(runner, markdown_file_path)

                _render_animation(future, f"{markdown_file_path.name}")
                future.result()  # check future result

                typer.echo(f"\rFinished    [{markdown_file_path.name}]")
                typer.echo("")  # new line

    typer.echo("\n")  # new line after progress bar
    typer.echo(f"Images successfully uploaded to S3\n")


if __name__ == "__main__":
    app()
