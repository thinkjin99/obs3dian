import re
from pathlib import Path
from hint import List, Generator


class MarkDownParser:
    def __init__(self) -> None:
        pass

    def get_image_names(self, file_name: str) -> List[str]:
        image_names = []
        patt = r"!\[\[(.*?)\.(png|jpg|jpeg|gif)\]\]"  # group 1 = file_name, group 2 = foramt

        with open(file_name) as f:
            while line := f.readline():
                if search_result := re.search(patt, line):
                    image_name = f"{search_result.group(1)}.{search_result.group(2)}"
                    image_names.append(image_name)

        return image_names

    def generate_image_paths(
        self, image_names: list[str]
    ) -> Generator[Path, None, None]:
        current_path = Path.cwd()
        image_name_set = set(image_names)
        suffixes = set((".png", ".jpg", ".jpeg", ".gif"))
        for file_path in current_path.rglob("**/*"):  # 모든 디렉토리 탐사
            if (
                file_path.suffix in suffixes and file_path.name in image_name_set
            ):  # 파일 이름이 존재한다면
                yield file_path

    def replace_image_link(self, file_name: str, link_map: List[tuple[str, str]]):
        with open(file_name, "r") as origin_file:  # 기존 파일
            output_file = open(f"output/{file_name}", "w")  # 수정 파일

            while line := origin_file.readline():
                for image_name, s3_url in link_map:
                    local_image_link = r"!\[\[" + image_name + r"\]\]"
                    if local_link := re.search(
                        local_image_link, line
                    ):  # 이미지 링크가 존재하는지 탐색
                        s3_link = f"![][{s3_url}]"
                        line = line.replace(
                            local_link.group(), s3_link
                        )  # s3 링크로 대체
                output_file.write(line)  # 복사 진행

            output_file.close()
