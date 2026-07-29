import re
from pathlib import Path
from dataclasses import dataclass
import shutil
import warnings
from typing import List, Callable, Tuple
from urllib.parse import unquote


@dataclass
class ImageText:
    """
    Data container for image.
    This class contains image file name, path and line number in markdown.
    """

    name: str
    line_no: int
    path: Path
    metadata: str
    source_text: str = ""
    s3_url: str | None = None

    def __post_init__(self):
        self.metadata = "" if not self.metadata else self.metadata


def _extract_image_from_no_path_patt(match_result: re.Match) -> dict:
    image_info = match_result.groupdict()
    image_name = image_info.get("name")
    assert image_name, "ImageText doesn't have path"
    image_info["source_text"] = match_result.group(0)
    return image_info


def _extract_image_from_path_patt(match_result: re.Match) -> dict | None:
    image_info = match_result.groupdict()
    image_path = image_info.get("path")
    assert image_path, "ImageText doesn't have path"
    if image_path[:4] in ("http", "https"):  # if link is external link
        return None

    try:
        image_info["name"] = unquote(Path(image_path).name)  # update imageText name
        image_info["source_text"] = match_result.group(0)
        return image_info

    except Exception:
        raise ValueError(f"{image_path} is invalid path")


def _extract_image_by_patt(
    func_patt_map: List[Tuple[Callable, str]],
    name_path_map: dict[str, Path],
    markdown_file_path: Path,
    line: str,
    line_no: int,
) -> List[dict]:

    image_infos: List[dict] = []
    for func, patt in func_patt_map:
        if match_results := re.finditer(patt, line):  # match pattern
            for match_result in match_results:
                if image_info := func(match_result):  # run match func for patt
                    try:
                        image_info["path"] = name_path_map[image_info["name"]]
                        image_info["line_no"] = line_no
                        image_infos.append(image_info)
                    except KeyError:  # image file could be not exists
                        warnings.warn(
                            f"{markdown_file_path}:{line_no + 1}: "
                            f"Image file not found: {image_info['name']}",
                            RuntimeWarning,
                            stacklevel=2,
                        )
                        continue

    return image_infos


def extract_images_from_md(
    markdown_file_path: Path, name_path_map: dict[str, Path]
) -> List[ImageText]:
    """
    Extract images from md file

    Args:
        markdown_file_path (Path): markdown file path
        name_path_map (dict[str, Path]): image name path map {abc.png : /foo/abc.png}

    Returns:
        List[ImageText]: Image data in markdown
    """
    extensions = r"png|jpg|jpeg|gif|webp"
    no_path_patt = rf"!\[\[(?P<name>[^]|]+\.(?:{extensions}))(?:\|(?P<metadata>[^]]+))?\]\]"
    path_patt = rf"!\[(?P<metadata>[^]]*)\]\((?P<path>[^)]+?\.(?:{extensions}))\)"

    func_patt_map: List[Tuple[Callable, str]] = [
        (_extract_image_from_no_path_patt, no_path_patt),
        (_extract_image_from_path_patt, path_patt),
    ]  # regex patt and match function

    images: List[ImageText] = []
    in_fenced_code = False
    with markdown_file_path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f):  # read lines
            if line.lstrip().startswith("```"):
                in_fenced_code = not in_fenced_code
                continue
            if in_fenced_code:
                continue

            inline_code_spans = [match.span() for match in re.finditer(r"`[^`]*`", line)]
            searchable_line = line
            for span_start, span_end in inline_code_spans:
                searchable_line = (
                    searchable_line[:span_start]
                    + " " * (span_end - span_start)
                    + searchable_line[span_end:]
                )
            image_infos = _extract_image_by_patt(
                func_patt_map,
                name_path_map,
                markdown_file_path,
                searchable_line,
                line_no,
            )
            for image_info in image_infos:
                images.append(ImageText(**image_info))

    return images


def get_images_name_path_map(image_folder_path: Path) -> dict[str, Path]:
    """
    get all images in folder and create [name, Path] dict of all iamges

    Args:
        image_folder_path (Path): imageText folder path

    Returns:
        dict[str, Path]: {name, Path}
    """
    supported_suffixes = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
    name_path_map: dict[str, Path] = {}
    # search all subfolders
    for file_path in image_folder_path.rglob("**/*"):
        if file_path.is_file() and file_path.suffix.lower() in supported_suffixes:
            name_path_map[file_path.name] = file_path
    return name_path_map


def write_md_file(
    markdown_file_path: Path,
    output_folder_path: Path,
    uploaded_images: List[ImageText],
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
    output_folder_path.mkdir(parents=True, exist_ok=True)
    with open(markdown_file_path, "r", encoding="utf-8") as origin_file:
        with open(out_file_path, "w", encoding="utf-8") as output_file:
            for line_no, line in enumerate(origin_file):
                for image in uploaded_images:
                    if line_no == image.line_no:
                        replacement = f"![{image.metadata}]({image.s3_url})"
                        line = line.replace(image.source_text, replacement, 1)
                output_file.write(line)  # if no replace just copy line

    if is_overwrite:
        shutil.move(out_file_path, markdown_file_path)
