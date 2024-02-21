import concurrent.futures
import json
from pathlib import Path

from code.s3 import S3
from code.markdown import *

from typing import Generator, List, Callable


def load_credentials() -> dict:
    root = Path.cwd()
    path = root.joinpath("credentials.json")
    with path.open("r") as f:
        credentials = json.load(f)
    return credentials


# def get_s3_keys(
#     s3: S3, markdown_file_path: Path, path_generator: Generator[Path, None, None]
# ) -> List[tuple[str, str]]:
#     # link_map = []
#     for image_path in path_generator:
#         key: str = s3.create_key(
#             markdown_file_path.name, image_path.name
#         )  # s3 업로드용 키 생성
#         # s3.put_image(key, image_path)  # s3에 로컬 이미지 업로드
#         # print(f"Upload image: {image_path.name}")
#         # link_map.append((image_path.name, s3.create_s3_url(key)))  # 로컬 링크, s3 url

#     return link_map


def create_obs3dian_runner() -> Callable:
    credentials: dict = load_credentials()
    s3 = S3(credentials["profile_name"], credentials["bucket_name"])

    def run_obs3dian(markdown_file_path: Path) -> None:
        path_generator: Generator = generate_local_paths(markdown_file_path)
        link_map = [
            (image_path, s3.create_key(markdown_file_path, image_path))
            for image_path in path_generator
        ]

        write_ouptut(markdown_file_path, credentials["output_path"], link_map)
        print(f"{markdown_file_path.name} is finished...")
        return

    return run_obs3dian


def run_mutiple(root: Path = Path.cwd()) -> None:
    run_obs3dian = create_obs3dian_runner()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for file_path in root.rglob("*.md"):  # 마크다운 파일 전체 적용
            future = executor.submit(run_obs3dian, file_path)
    return


if __name__ == "__main__":
    run_mutiple(Path("test"))
    # run_ = run()
    # run_(Path("os/메모리.md"))
