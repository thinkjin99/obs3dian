import concurrent.futures
from pathlib import Path
from typing import Callable, List

from .markdown import (
    get_images_name_path_map,
    write_md_file,
    extract_images_from_md,
    ImageText,
)
from .s3 import S3


def _upload_images_from_md(
    s3: S3, markdown_path: Path, images: List[ImageText]
) -> List[ImageText]:
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
        for image in images:
            if image.path:
                futures.append(
                    executor.submit(s3.put_image, markdown_path, image)
                )  # run upload by multithread

        uploaded_images: List[ImageText] = []  # put success image path list
        for future in concurrent.futures.as_completed(futures, timeout=60):
            uploaded_images.append(future.result())

    return uploaded_images


def create_obs3dian_runner(
    s3: S3,
    image_folder_path: Path,
    output_folder_path: Path,
    is_overwrite: bool = False,
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

    name_path_map: dict[str, Path] = get_images_name_path_map(image_folder_path)

    def run(markdown_file_path: Path) -> None:
        """
        Run obs3dian command extract image paths and replace them by S3 URLs.

        Args:
            markdown_file_path (Path): mark down file path
        """
        images: List[ImageText] = extract_images_from_md(
            markdown_file_path, name_path_map
        )
        uploaded_images = _upload_images_from_md(s3, markdown_file_path, images)
        write_md_file(
            markdown_file_path, output_folder_path, uploaded_images, is_overwrite
        )  # write new md with S3 link
        return

    return run
