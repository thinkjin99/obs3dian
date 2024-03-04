import pytest
import pathlib
from obs3dian.main import run


class TestRun:
    user_input_path = pathlib.Path("./test_files")

    def test_by_profile_run(self):
        # test by profile
        run(user_input_path=self.user_input_path, overwrite=False, useprofile=True)

    def test_by_keys(self):
        # test with access key
        run(user_input_path=self.user_input_path, overwrite=False, useprofile=False)

    pass
