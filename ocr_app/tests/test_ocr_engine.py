"""Tests for the line-reconstruction logic (no PaddleOCR needed).

Run:  python -m pytest ocr_app/tests/ -q
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ocr_app.core.ocr_engine import OCREngine  # noqa: E402


def _box(x, y, w=50, h=20):
    return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]


def test_sort_top_to_bottom_left_to_right():
    # Two visual lines; second line's words given out of order.
    block = [
        [_box(10, 5), ("Привет", 0.99)],
        [_box(120, 8), ("мир", 0.98)],
        [_box(200, 60), ("второй", 0.97)],
        [_box(10, 62), ("Hello", 0.99)],
    ]
    text = OCREngine._sort_lines(block)
    assert text == "Привет\nмир\nHello\nвторой"


def test_same_line_grouping_within_tolerance():
    # y differs by < 15px -> same line, ordered by x.
    block = [
        [_box(300, 12), ("C", 0.9)],
        [_box(10, 4), ("A", 0.9)],
        [_box(150, 9), ("B", 0.9)],
    ]
    assert OCREngine._sort_lines(block) == "A\nB\nC"


def test_empty_block():
    assert OCREngine._sort_lines([]) == ""
