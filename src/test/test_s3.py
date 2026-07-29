from pathlib import Path
from types import SimpleNamespace

from obs3dian.markdown import ImageText
from obs3dian.s3 import S3


class FakeClient:
    def __init__(self):
        self.meta = SimpleNamespace(region_name="ap-northeast-2")
        self.request = None

    def put_object(self, **kwargs):
        self.request = kwargs


def test_put_image_uses_clean_key_and_correct_content_type(tmp_path: Path):
    path = tmp_path / "photo.png"
    path.write_bytes(b"png")
    client = FakeClient()
    s3 = S3.__new__(S3)
    s3.bucket_name = "bucket"
    s3.session = SimpleNamespace(region_name="ap-northeast-2")
    s3.s3 = client
    image = ImageText("photo.png", 0, path, "")

    uploaded = s3.put_image(Path("포트폴리오.md"), image)

    assert client.request["Key"] == "포트폴리오/photo.png"
    assert client.request["ContentType"] == "image/png"
    assert "%ED%8F%AC%ED%8A%B8%ED%8F%B4%EB%A6%AC%EC%98%A4/photo.png" in uploaded.s3_url
