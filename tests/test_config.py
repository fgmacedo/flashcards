# coding: utf-8
import pytest
from reportlab.lib.colors import HexColor, PCMYKColor


@pytest.fixture
def parse_color():
    from flashcards.__main__ import parse_color
    return parse_color


@pytest.mark.parametrize('color_value, expected_color', [
    ('0,100,100,10', PCMYKColor(0, 100, 100, 10), ),
    ('5,10,15,20', PCMYKColor(5, 10, 15, 20), ),
    ('#ff0000', HexColor('0xff0000'), ),
])
def test_config(parse_color, color_value, expected_color):
    color = parse_color(color_value)
    assert color == expected_color
