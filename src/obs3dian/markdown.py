import re
from pathlib import Path
from dataclasses import dataclass
import shutil
from typing import Generator, List, Callable, Tuple


@dataclass
class ImageText:
    name: str
    line: int
    path: Path
    metadata: str | None = None


def _extract_image_from_no_path_patt(match_result: re.Match) -> dict:
    image_info = match_result.groupdict()
    image_name = image_info.get("name")
    assert image_name, "ImageText doesn't have path"
    return image_info


def _extrace_image_from_path_patt(match_result: re.Match) -> dict | None:
    image_info = match_result.groupdict()
    image_path = image_info.get("path")
    assert image_path, "ImageText doesn't have path"
    if image_path[:4] in ("http", "https"):  # if link is external link
        return None

    try:
        image_info["name"] = Path(image_path).name  # update imageText name
        return image_info

    except Exception:
        raise ValueError(f"{image_path} is invalid path")


def extract_images_from_md(
    markdown_file_path: Path, name_path_map: dict[str, Path]
) -> List[ImageText]:
    """
    Get imageText names from .md file

    Args:
        markdown_file_path (Path): md file path

    Returns:
        List[str]: imageText names in md file
    """
    no_path_patt = r"!\[\[(?P<name>[^]]+\.(png|jpg|jpeg|gif))\|?(?P<metadata>[^]]+)?\]\]"  # group 1 = file_name, group 2 = foramt, group3 = imageText metadata
    path_patt = r"!\[(?P<metadata>[^]]+)\]\((?P<path>[^)]+\.png|jpg|jpeg|gif\))"  # group 1 = metadata group 2 = file path

    func_patt_map: List[Tuple[Callable, str]] = [
        (_extract_image_from_no_path_patt, no_path_patt),
        (_extrace_image_from_path_patt, path_patt),
    ]  # regex patt and match function

    images: List[ImageText] = []
    with markdown_file_path.open("r") as f:
        for i, line in enumerate(f):  # read lines
            for func, patt in func_patt_map:
                if match_results := re.finditer(patt, line):  # match pattern
                    for match_result in match_results:
                        if image_info := func(match_result):
                            image_path = Path(name_path_map[image_info["name"]])
                            images.append(
                                ImageText(**image_info, path=image_path, line=i)
                            )  # append imageText data
    return images


def get_images_name_path_map(image_folder_path: Path) -> dict[str, Path]:
    """
    get all images in folder and create [name, Path] dict of all iamges

    Args:
        image_folder_path (Path): imageText folder path

    Returns:
        dict[str, Path]: {name, Path}
    """
    patt = r".*\.(png|jpg|jpeg|gif)$"
    name_path_map: dict[str, Path] = {}
    # search all subfolders
    for file_path in image_folder_path.rglob("**/*"):
        if re.search(patt, file_path.suffix):
            name_path_map[file_path.name] = file_path
    return name_path_map


def _replace_name_to_url(line: str, image_name: str, s3_url: str):
    # Local file link -> S3 url
    local_image_patt = rf"!\[\[({image_name})\|?(.*)?\]\]"
    if matched := re.search(local_image_patt, line):  # 이미지 링크가 존재하는지 탐색
        if len(matched.group()) > 1:
            image_meta_data = matched.group(2)

        replace_str = f"![{image_meta_data}]({s3_url})"
        line = line.replace(matched.group(), replace_str)  # s3 링크로 대체
    return line


def write_md_file(
    markdown_file_path: Path,
    output_folder_path: Path,
    link_replace_map: List[tuple[str, str]],
    is_overwrite: bool = False,
):
    """
    Write new .md that replace local file link to S3 url.
    Only replace imageText file link and other things are same
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

    if is_overwrite:
        shutil.move(out_file_path, markdown_file_path)
