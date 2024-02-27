import concurrent.futures as concurrent_futures

import typer
from typing_extensions import Annotated

from pathlib import Path
import time

from .core import create_obs3dian_runner
from .config import load_configs, save_config, APP_NAME, Configuration
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
    Apply settings from config.json file

    Raises:
        e: invalid output path
    """
    configs: Configuration = load_configs()
    output_folder_path = _convert_path_absoulte(
        Path(configs.output_folder_path), strict=False
    )

    s3 = S3(
        configs.profile_name,
        configs.aws_access_key,
        configs.aws_secret_key,
        configs.bucket_name,
    )
    print("Connected to AWS S3")

    if s3.create_bucket():
        print(f"Bucket {configs.bucket_name} created")
        print("Bucket has public read access so anyone can see files in your bucket")
        s3.put_public_access_policy()
    else:
        print(f"Bucket {configs.bucket_name} is already exists")

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


@app.command()
def run(
    user_input_path: Path,
    overwrite: Annotated[
        bool, typer.Option(help="Overwrite original md file default is create new file")
    ],
):
    """
    Run obs3dian main command, get image local file paths from md file.
    After extracting image paths, it uploads images to s3 and replaces all file links in .md to S3 links.
    Outputs will be wrriten under output folder and it's image links would replaced to S3 links

    Args:
        user_input_path (Path): user input path
    """

    apply()  # run apply
    typer.echo("")  # new line

    user_input_path = _convert_path_absoulte(user_input_path)
    configs: Configuration = load_configs()
    output_folder_path = _convert_path_absoulte(Path(configs.output_folder_path))
    s3 = S3(
        configs.profile_name,
        configs.aws_access_key,
        configs.aws_secret_key,
        configs.bucket_name,
    )

    runner = create_obs3dian_runner(
        s3, Path(configs.image_folder_path), output_folder_path, overwrite
    )  # create main function

    if user_input_path.is_dir():
        markdown_file_paths = [
            markdown_path for markdown_path in user_input_path.rglob("**/*.md")
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
    typer.echo(
        f"Total converts: {len(markdown_file_paths)}\nobs3dian is successfully finished\n"
    )


if __name__ == "__main__":
    app()
