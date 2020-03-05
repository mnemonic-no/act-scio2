""" test feed download """

from act.scio.feeds import download


def test_safe_download() -> None:
    """ test for safe download """
    assert download.safe_filename("test%.[x y z]") == "test.x_y_z"
