import concurrent.futures
from pathlib import Path

from src.markdown import generate_local_paths, write_md_file
from src.s3 import S3

from typing import Generator, Callable, List, Tuple


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
            s3_key = s3.create_s3_key(markdown_file_name, path.name)  # create Key
            futures.append(
                executor.submit(s3.put_image, path, s3_key)
            )  # run upload by multithread

        put_image_paths: List[Path] = []  # put success image path list
        for future in concurrent.futures.as_completed(futures, timeout=60):
            try:
                put_image_paths.append(future.result())
            except Exception as e:
                print(e)
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

        # (image name, S3 URL) to convert link
        link_replace_pairs: List[Tuple[str, str]] = []
        for image_path in put_image_paths:
            image_name = image_path.name
            s3_url = s3.get_image_url(markdown_file_name, image_name)
            link_replace_pairs.append(
                (image_name, s3_url)
            )  # image name in .md would convert to S3 url

        write_md_file(
            markdown_file_path, output_folder_path, link_replace_pairs
        )  # write new md with S3 link
        return

    return run
