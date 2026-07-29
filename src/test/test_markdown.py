from pathlib import Path

import pytest

from obs3dian.markdown import extract_images_from_md, get_images_name_path_map, write_md_file


def test_extract_and_replace_images_without_destroying_line(tmp_path: Path):
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    (image_dir / "first.png").write_bytes(b"png")
    (image_dir / "second.jpeg").write_bytes(b"jpeg")
    markdown = tmp_path / "portfolio.md"
    markdown.write_text(
        "before ![[first.png|500]] middle ![caption](./second.jpeg) after\n"
        "`![[example.png]]`\n"
        "```md\n![[first.png]]\n```\n",
        encoding="utf-8",
    )

    images = extract_images_from_md(markdown, get_images_name_path_map(image_dir))

    assert [image.name for image in images] == ["first.png", "second.jpeg"]
    images[0].s3_url = "https://bucket/first.png"
    images[1].s3_url = "https://bucket/second.jpeg"
    output_dir = tmp_path / "nested" / "output"
    write_md_file(markdown, output_dir, images)
    result = (output_dir / markdown.name).read_text(encoding="utf-8")
    assert "before ![500](https://bucket/first.png) middle ![caption](https://bucket/second.jpeg) after" in result
    assert "`![[example.png]]`" in result
    assert "```md\n![[first.png]]\n```" in result


def test_missing_image_emits_warning(tmp_path: Path):
    markdown = tmp_path / "portfolio.md"
    markdown.write_text("![[missing.png]]\n", encoding="utf-8")

    with pytest.warns(RuntimeWarning, match=r"portfolio\.md:1: Image file not found: missing\.png"):
        assert extract_images_from_md(markdown, {}) == []


def test_image_map_is_case_insensitive_and_supports_webp(tmp_path: Path):
    (tmp_path / "PHOTO.PNG").write_bytes(b"png")
    (tmp_path / "photo.webp").write_bytes(b"webp")
    assert set(get_images_name_path_map(tmp_path)) == {"PHOTO.PNG", "photo.webp"}
