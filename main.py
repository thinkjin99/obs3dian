import typer
from pathlib import Path
from code.main import run, run_mutiple
from code.config import load_credentials


def init():
    pass


def main(path: Path):
    credentials = load_credentials()
    path = path.absolute().resolve(strict=True)

    if path.is_dir():
        run_mutiple(credentials, path)
    else:
        run(credentials)


if __name__ == "__main__":
    typer.run(main)
