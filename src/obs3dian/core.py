import concurrent.futures
from pathlib import Path

from .markdown import create_image_path_generator, write_md_file
from .s3 import S3

from typing import Generator, Callable, List, Tuple


def put_images_in_md(
    s3: S3, markdown_path: Path, image_path_generator: Generator[Path, None, None]
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
        for image_path in image_path_generator:
            futures.append(
                executor.submit(s3.put_image, markdown_path, image_path)
            )  # run upload by multithread

        put_image_paths: List[Path] = []  # put success image path list
        for future in concurrent.futures.as_completed(futures, timeout=60):
            try:
                put_image_paths.append(future.result())
            except Exception as e:
                print(e)
                continue

    return put_image_paths


def create_obs3dian_runner(
    s3: S3, image_folder_path: Path, output_folder_path: Path
) -> Callable:
    """
    Create runner fucntion object
    S3 controller and ouput_folder_path would not change before config

    Args:
        s3 (S3): S3 controller
        image_folder_path (Path): image folder path
        output_folder_path (Path): output folder path

    Returns:
        Callable: runner
    """

    image_path_creator: Callable = create_image_path_generator(
        image_folder_path
    )  # function to make image path generator

    def run(markdown_file_path: Path) -> None:
        """
        Run obs3dian command extract image paths and replace them by S3 URLs.

        Args:
            markdown_file_path (Path): mark down file path
        """
        image_path_generator: Generator = image_path_creator(markdown_file_path)
        put_image_paths = put_images_in_md(s3, markdown_file_path, image_path_generator)

        # (image name, S3 URL) to convert link
        link_replace_pairs: List[Tuple[str, str]] = []
        for image_path in put_image_paths:
            image_name = image_path.name
            s3_url = s3.get_image_url(markdown_file_path, image_path)
            link_replace_pairs.append(
                (image_name, s3_url)
            )  # image name in .md would convert to S3 url

        write_md_file(
            markdown_file_path, output_folder_path, link_replace_pairs
        )  # write new md with S3 link
        return

    return run
