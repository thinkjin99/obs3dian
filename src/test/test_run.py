import pytest
import pathlib
from obs3dian.main import run


class TestRun:
    user_input_path = pathlib.Path("/Users/jin/Programming/project/obs3dian/test_files")

    def test_by_profile_run(self):
        # test by profile
        run(user_input_path=self.user_input_path, overwrite=False, usekey=False)

    def test_by_keys(self):
        # test with access key
        run(user_input_path=self.user_input_path, overwrite=False, usekey=True)
