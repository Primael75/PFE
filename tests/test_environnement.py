import sys


def test_version_python():
    assert sys.version_info[:2] == (3, 12)
