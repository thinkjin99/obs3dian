from pathlib import Path
from unittest.mock import Mock, patch

from typer.testing import CliRunner

from obs3dian.config import Configuration
from obs3dian.main import app


def test_cli_help_renders():
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0, result.output


def test_run_uses_stored_credentials_and_creates_output(tmp_path: Path):
    markdown = tmp_path / "portfolio.md"
    markdown.write_text("portfolio", encoding="utf-8")
    output_dir = tmp_path / "missing" / "output"
    config = Configuration(
        aws_access_key="access",
        aws_secret_key="secret",
        bucket_name="bucket",
        output_folder_path=str(output_dir),
        image_folder_path=str(tmp_path),
    )
    fake_s3 = Mock()
    processed = []

    with (
        patch("obs3dian.main.load_configs", return_value=config),
        patch("obs3dian.main.set_bucket") as set_bucket,
        patch("obs3dian.main.S3", return_value=fake_s3) as s3_class,
        patch("obs3dian.main.create_obs3dian_runner", return_value=processed.append),
    ):
        result = CliRunner().invoke(app, ["run", str(markdown)])

    assert result.exit_code == 0, result.output
    assert output_dir.is_dir()
    set_bucket.assert_called_once_with("bucket", None, "access", "secret")
    s3_class.assert_called_once_with(
        profile_name=None,
        aws_access_key="access",
        aws_secret_key="secret",
        bucket_name="bucket",
    )
    assert processed == [markdown.resolve()]
