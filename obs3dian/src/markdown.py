import re
from pathlib import Path

from typing import Generator, List


def _get_image_names(markdown_file_path: Path) -> List[str]:
    """
    Get image names from .md file

    Args:
        markdown_file_path (Path): md file path

    Returns:
        List[str]: image names in md file
    """
    image_names = []
    patt = (
        r"!\[\[(.*?)\.(png|jpg|jpeg|gif)\]\]"  # group 1 = file_name, group 2 = foramt
    )
    with markdown_file_path.open("r") as f:
        while line := f.readline():
            if search_results := re.findall(patt, line):
                for search_result in search_results:
                    image_name = f"{search_result[0]}.{search_result[1]}"  # extract abc.png like names
                    image_names.append(image_name)
    return image_names


def generate_local_image_paths(
    image_folder_path: Path, markdown_file_path: Path
) -> Generator[Path, None, None]:
    """
    Create Genrator yields image path in md file

    Args:
        image_folder_path (Path): image folder path
        markdown_file_path (Path): md file path

    Yields:
        Generator[Path, None, None]: yield image path generator
    """
    image_names: list[str] = _get_image_names(markdown_file_path)
    image_name_set = set(image_names)
    suffixes = set((".png", ".jpg", ".jpeg", ".gif"))

    # TODO use trie or something code is inefficient
    for file_path in image_folder_path.rglob("**/*"):  # search all subfolders
        if (
            file_path.suffix in suffixes and file_path.name in image_name_set
        ):  # 파일 이름이 존재한다면
            yield file_path


def _replace_name_to_url(line: str, image_name: str, s3_url: str):
    # Local file link -> S3 url
    local_image_link = r"!\[\[" + image_name + r"\]\]"
    if local_link := re.search(local_image_link, line):  # 이미지 링크가 존재하는지 탐색
        s3_link = f"![][{s3_url}]"
        line = line.replace(local_link.group(), s3_link)  # s3 링크로 대체
    return line


def write_md_file(
    markdown_file_path: Path,
    output_folder_path: Path,
    link_replace_map: List[tuple[str, str]],
):
    """
    Write new .md that replace local file link to S3 url.
    Only replace image file link and other things are same
    Args:
        markdown_file_path (Path): md file path
        output_folder_path (Path): output file path
        link_replace_map (List[tuple[str, str]]): file link -> s3 url
    """
    out_file_path = output_folder_path.joinpath(markdown_file_path.name)
    with open(markdown_file_path, "r") as origin_file:  # open origin file
        with open(out_file_path, "w") as output_file:
            while line := origin_file.readline():
                for image_name, s3_url in link_replace_map:
                    line = _replace_name_to_url(line, image_name, s3_url)
                output_file.write(line)  # if no replace just copy line
