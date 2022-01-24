""" test feed download """

from act.scio.feeds import extract


def test_safe_download() -> None:
    """test for safe download"""
    assert extract.safe_filename("test%.[x y z]") == "test.x_y_z"
