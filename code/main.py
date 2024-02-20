from pathlib import Path
from s3 import S3
from markdown_parser import MarkDownParser
import concurrent.futures

from hint import Generator, List


def create_maps(
    s3: S3, markdown_file_name: str, path_generator: Generator[Path, None, None]
) -> List[tuple[str, str]]:
    link_map = []
    for image_path in path_generator:
        key: str = s3.create_key(markdown_file_name, image_path.name)
        s3.put_image(key, image_path)  # s3에 로컬 이미지 업로드
        print(f"Upload image: {image_path.name}")
        link_map.append((image_path.name, s3.create_s3_url(key)))  # 로컬 링크, s3 url
    return link_map


def parse_md(mp: MarkDownParser, md_file_name: str):
    image_names: List[str] = mp.get_image_names(
        md_file_name
    )  # 마크다운 파일 내부 이미지 파일 이름
    path_generator = mp.generate_image_paths(image_names)  # 해당 파일의 경로
    return path_generator


def run(profile_name: str = "default", bucket_name: str = "obs3dian"):
    markdown_parser = MarkDownParser()
    s3 = S3(profile_name, bucket_name)

    def wrapper(markdown_file_name: str):
        path_generator: Generator = parse_md(markdown_parser, markdown_file_name)
        link_map: List[tuple[str, str]] = create_maps(
            s3, markdown_file_name, path_generator
        )  # 이미지 이름, S3 url
        markdown_parser.replace_image_link(markdown_file_name, link_map)
        print(f"{markdown_file_name} is finished...")

    return wrapper


def run_mutiple(root: Path = Path.cwd()):
    run_ = run()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for file_path in root.glob("*.md"):  # 마크다운 파일 전체 적용
            future = executor.submit(run_, file_path.name)
            # future.result()


if __name__ == "__main__":
    run_mutiple()
