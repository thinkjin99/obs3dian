import concurrent.futures
from pathlib import Path

from src.markdown import generate_local_paths, write_md_file
from src.s3 import S3

from typing import Generator, Callable, List


def create_s3_key(markdown_file_name: str, path: Path) -> str:
    return f"{markdown_file_name}/{path.name}"


def put_images_in_md(
    s3: S3, markdown_file_name: str, path_generator: Generator[Path, None, None]
) -> List[Path]:
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        for path in path_generator:  # s3 key
            s3_key = create_s3_key(markdown_file_name, path)
            futures.append(executor.submit(s3.put_image, path, s3_key))

        links_map = []
        for future in concurrent.futures.as_completed(futures):
            try:
                links_map.append(future.result())
            except Exception as e:
                print("Erorr Occured: ", str(e))

    return links_map


def create_obs3dian_runner(s3: S3, output_folder_path: Path) -> Callable:
    def run_obs3dian(markdown_file_path: Path) -> None:
        path_generator: Generator = generate_local_paths(markdown_file_path)
        markdown_file_name = markdown_file_path.stem

        uploaded_image_paths = put_images_in_md(s3, markdown_file_name, path_generator)

        link_replace_map = [
            (path.name, s3.get_s3_url(create_s3_key(markdown_file_name, path)))
            for path in uploaded_image_paths
        ]

        write_md_file(markdown_file_path, output_folder_path, link_replace_map)
        return

    return run_obs3dian
