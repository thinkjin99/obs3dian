import pytest
import pathlib
from obs3dian.markdown import extract_images_from_md, get_images_name_path_map


class TestRun:
    user_input_path = pathlib.Path(
        "/Users/jin/Programming/project/obs3dian/src/test/test_files"
    )

    def test_regex(self):
        markdown_path = self.user_input_path / "test_png.md"
        name_path_map = get_images_name_path_map(self.user_input_path)
        images = extract_images_from_md(markdown_path, name_path_map)
        print(images)
