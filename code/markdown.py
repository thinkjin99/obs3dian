import re
from pathlib import Path

from typing import Generator, List


def _get_image_names(markdown_file_path: Path) -> List[str]:
    image_names = []
    patt = (
        r"!\[\[(.*?)\.(png|jpg|jpeg|gif)\]\]"  # group 1 = file_name, group 2 = foramt
    )
    with markdown_file_path.open("r") as f:
        while line := f.readline():
            if search_results := re.findall(patt, line):
                for search_result in search_results:
                    image_name = (
                        f"{search_result[0]}.{search_result[1]}"  # abc.png 추출
                    )
                    image_names.append(image_name)
    return image_names


def generate_local_paths(markdown_file_path: Path) -> Generator[Path, None, None]:
    current_path = Path.cwd()
    image_names: list[str] = _get_image_names(markdown_file_path)
    image_name_set = set(image_names)
    suffixes = set((".png", ".jpg", ".jpeg", ".gif"))
    for file_path in current_path.rglob("**/*"):  # 모든 디렉토리 탐사
        if (
            file_path.suffix in suffixes and file_path.name in image_name_set
        ):  # 파일 이름이 존재한다면
            yield file_path


def _replace_local_paths(line: str, link_map: List[tuple[str, str]]):
    # Local -> s3로 이미지 링크 변경
    for image_name, s3_url in link_map:
        local_image_link = r"!\[\[" + image_name + r"\]\]"
        if local_link := re.search(
            local_image_link, line
        ):  # 이미지 링크가 존재하는지 탐색
            s3_link = f"![][{s3_url}]"
            line = line.replace(local_link.group(), s3_link)  # s3 링크로 대체
    return line


def write_ouptut(
    markdown_file_path: Path, output_path: Path, link_map: List[tuple[str, str]]
):
    out_file_path = output_path.joinpath(markdown_file_path.name)  # 수정 파일 경로
    with open(markdown_file_path, "r") as origin_file:  # 기존 파일
        with open(out_file_path, "w") as output_file:
            while line := origin_file.readline():
                output_file.write(
                    _replace_local_paths(line, link_map)
                )  # if no replace just copy line