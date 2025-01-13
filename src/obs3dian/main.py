import concurrent.futures as concurrent_futures
from threading import Event, Thread

import typer
from typing_extensions import Annotated
from typing import Optional

from pathlib import Path
import time

from .core import create_obs3dian_runner
from .config import load_configs, save_config, remove_config, APP_NAME, Configuration
from .s3 import S3


app = typer.Typer(name=APP_NAME)


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


@app.command()
def set_output_folder(output_folder_path: str):
    output_folder_path_ = _convert_path_absoulte(Path(output_folder_path), strict=False)
    if not output_folder_path_.exists():
        try:
            output_folder_path_.mkdir()
            print(f"Create Output Folder in {output_folder_path_.name}")
            return True

        except OSError as e:
            print(f"Output path {output_folder_path} is invalid")
            raise e
    else:
        print("Output Folder is already exists (Can modify by run obs3dian config)")


@app.command()
def set_bucket(
    bucket_name: str,
    profile_name: Optional[str] = None,
    aws_access_key: Optional[str] = None,
    aws_secret_key: Optional[str] = None,
):
    """
    Apply settings from config.json file

    Raises:
        e: invalid output path
    """
    if profile_name:
        s3 = S3(
            profile_name=profile_name,
            bucket_name=bucket_name,
        )
    elif aws_access_key and aws_secret_key:
        s3 = S3(
            bucket_name=bucket_name,
            aws_access_key=aws_access_key,
            aws_secret_key=aws_secret_key,
        )

    if s3.create_bucket():
        print(f"Bucket {bucket_name} created")
        print("Bucket has public read access so anyone can see files in your bucket")
    else:
        print(f"Bucket {bucket_name} is already exists try with other name")


@app.command()
def config(
    reset: Annotated[
        bool,
        typer.Option(help="Reset config.json file"),
    ] = False,
):
    """
    Writes config file. This command sets setting for run obs3dian.
    It should be executed first before run obs3dian.
    If you want to apply setting use command 'apply'
    If you just enter the setting doesn't change
    """
    if reset:
        remove_config()  # save empty data to reset config file
        return

    default_input = (
        lambda description, default: input(f"{description} [{default}]: ").strip()
        or default
    )
    try:
        # Last config data
        configs: Configuration = load_configs()

    except FileNotFoundError:
        configs: Configuration = Configuration()

    profile_name = configs.profile_name
    aws_access_key = configs.aws_access_key
    aws_secret_key = configs.aws_secret_key
    bucket_name = configs.bucket_name
    output_path = configs.output_folder_path
    image_folder_path = configs.image_folder_path

    typer.echo("AWS-CLI profile name or AWS key is required")
    if input("Do you want to config AWS-CLI profile name? (Y/N): ") in ["y", "Y"]:
        profile_name = default_input("AWS CLI Profile Name", profile_name)

    else:
        aws_access_key = default_input("AWS AccessKey", aws_access_key)
        aws_secret_key = default_input("AWS Secret Key", aws_secret_key)
        if not (aws_access_key and aws_secret_key):
            raise ValueError("You must provide both access and secret key")

    bucket_name = default_input("S3 bucket Name", bucket_name)

    output_path = Path(default_input("Output Path", output_path))
    output_path = _convert_path_absoulte(output_path, False)

    image_folder_path = Path(default_input("Image Folder Path", image_folder_path))
    image_folder_path = _convert_path_absoulte(image_folder_path, True)

    json_data = {
        "profile_name": profile_name,
        "aws_access_key": aws_access_key,
        "aws_secret_key": aws_secret_key,
        "bucket_name": bucket_name,
        "output_folder_path": str(output_path),
        "image_folder_path": str(image_folder_path),
    }

    save_config(json_data)


def _render_animation(echo_text: str, event: Event) -> None:
    """
    Rendering loading animation

    Args:
        future (concurrent_futures.Future): future to wait
        description (str): description text to echo in terminal
    """
    i = 0
    animation = ["|", "/", "--", "\\"]
    while True:  # run until uploading is done
        typer.echo(
            f"\r{animation[i % len(animation)]:<2} {echo_text[:20]:<20}", nl=False
        )  # render animation like => | abc.md -> / abc.md -> -- abc.md
        time.sleep(0.2)  # give delay to show animation
        i += 1
    return


@app.command()
def run(
    md_file_path: Path,
    overwrite: Annotated[
        bool,
        typer.Option(
            help="Overwrites original md file in same file path. (default is creating new file under output folder)"
        ),
    ] = False,
    bucket_name: Annotated[
        Optional[str], typer.Option(help="Aws S3 Bucket Name")
    ] = None,
    aws_access_key: Annotated[
        Optional[str], typer.Option(help="AWS Access Key to use")
    ] = None,
    aws_secret_key: Annotated[
        Optional[str], typer.Option(help="AWS Secret Key to use")
    ] = None,
    profile_name: Annotated[
        Optional[str], typer.Option(help="Aws CLI Profile Name")
    ] = None,
    output_folder_path: Annotated[
        Optional[str], typer.Option(help="Converted Output Folder Path")
    ] = None,
    image_folder_path: Annotated[
        Optional[str], typer.Option(help="Image File Folder Path")
    ] = None,
):
    """
    Get images local file paths from md files in given path.
    After extracting image paths, it uploads images to S3 and replaces all file links in .md to S3 links.
    Outputs will be wrriten under output folder and it's image links would replaced to S3 links

    Args:
        absolute_md_file_path (Path): your markdown file path to convert. (dir or file)
    """

    configs: Configuration = load_configs()
    bucket_name = bucket_name or configs.bucket_name
    if output_folder_path:
        set_output_folder(output_folder_path)
    if bucket_name:
        set_bucket(bucket_name, profile_name, aws_access_key, aws_secret_key)
    typer.echo("")  # new line

    absolute_md_file_path = _convert_path_absoulte(md_file_path)
    output_folder_path = output_folder_path or configs.output_folder_path
    image_folder_path = image_folder_path or configs.image_folder_path

    s3 = S3(
        profile_name=profile_name,
        aws_access_key=aws_access_key,
        aws_secret_key=aws_secret_key,
        bucket_name=configs.bucket_name,
    )

    runner = create_obs3dian_runner(
        s3, Path(image_folder_path), Path(output_folder_path), overwrite
    )  # create main function

    if absolute_md_file_path.is_dir():
        markdown_file_paths = [
            markdown_path for markdown_path in md_file_path.rglob("**/*.md")
        ]  # get all .md file under input dir
    else:
        markdown_file_paths = [md_file_path]

    assert len(
        markdown_file_paths
    ), f"No md files in {md_file_path}"  # raise error when no md file in input path
    event = Event()
    animation_thread = Thread(
        target=_render_animation, args=("Processing files...", event), daemon=True
    )

    with concurrent_futures.ThreadPoolExecutor(
        max_workers=8
    ) as executor:  # thread for aniamtion
        futures = {
            executor.submit(runner, markdown_file_path): markdown_file_path
            for markdown_file_path in markdown_file_paths
        }
        typer.echo("")  # new line
        animation_thread.start()  # start loading animaton thread

        with typer.progressbar(
            label="Processing", iterable=futures.items(), show_eta=False
        ) as progeress:  # typer progress bar
            for future, markdown_file_path in progeress:
                # print progress bar
                typer.echo("")  # new line
                future.result()  # check future result
                typer.echo(f"\rFinished    [{markdown_file_path.name}]")

    typer.echo("\n")  # new line after progress bar
    typer.echo(
        f"Total converts: {len(markdown_file_paths)}\nobs3dian is successfully finished\n"
    )


if __name__ == "__main__":
    app()
