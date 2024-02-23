import concurrent.futures
from pathlib import Path

from src.markdown import generate_local_paths, write_md_file
from src.s3 import S3

from typing import Generator, Callable, List


def create_s3_key(markdown_file_name: str, image_name: str) -> str:
    """
    Create key by makrdown file name and image name key is used in S3

    Args:
        markdown_file_name (str): mark down file name
        image_name (str): image file name in markdown

    Returns:
        str: S3 key
    """
    return f"{markdown_file_name}/{image_name}"


def put_images_in_md(
    s3: S3, markdown_file_name: str, image_path_generator: Generator[Path, None, None]
) -> List[Path]:
    """
    Generate local images path by using generator and put images to S3.
    Return sccessfully put image paths

    Args:
        s3 (S3): instance to control S3
        markdown_file_name (str): makrdown file name
        image_path_generator (Generator[Path, None, None]): yield image paths to upload

    Returns:
        List[Path]: sccessfully put image paths
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        for path in image_path_generator:
            s3_key = create_s3_key(markdown_file_name, path.name)  # create Key
            futures.append(
                executor.submit(s3.put_image, path, s3_key)
            )  # run upload by multithread

        put_image_paths: List[Path] = []  # put success image path list
        for future in concurrent.futures.as_completed(futures):
            try:
                put_image_paths.append(future.result())
            except Exception as e:
                continue

    return put_image_paths


def create_obs3dian_runner(s3: S3, output_folder_path: Path) -> Callable:
    """
    Create runner fucntion object
    S3 controller and ouput_folder_path would not change before config

    Args:
        s3 (S3): S3 controller
        output_folder_path (Path): output folder path

    Returns:
        Callable: runner
    """

    def run(markdown_file_path: Path) -> None:
        """
        Run obs3dian command extract image paths and replace them by S3 URLs.

        Args:
            markdown_file_path (Path): mark down file path
        """
        image_path_generator: Generator = generate_local_paths(markdown_file_path)
        markdown_file_name = markdown_file_path.stem

        put_image_paths = put_images_in_md(s3, markdown_file_name, image_path_generator)

        link_replace_pairs = [
            (path.name, s3.get_s3_url(create_s3_key(markdown_file_name, path.name)))
            for path in put_image_paths
        ]  # get (local image path, S3 URL) to convert link

        write_md_file(markdown_file_path, output_folder_path, link_replace_pairs)
        return

    return run
