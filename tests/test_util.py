import pytest

from llmpdf.util import parse_pages


def test_parse_pages():
    assert parse_pages("1,2,5") == ["1", "2", "5"]
    assert parse_pages("1-4") == ["1", "2", "3", "4"]
    assert parse_pages("1,2,6-8") == ["1", "2", "6", "7", "8"]
