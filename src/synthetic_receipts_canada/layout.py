"""A receipt as a list of text lines on fixed-width thermal paper.

Thermal printers print a fixed number of columns: 42 on 80 mm paper, 32 on 58 mm. Every
layout helper here works in columns, so the same receipt renders identically whether it is
drawn to an image or dumped as plain text for extractor tests that skip OCR.
"""

from dataclasses import dataclass, field
from enum import Enum


class Align(Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class Size(Enum):
    NORMAL = 1
    DOUBLE = 2  # double height and width, as thermal printers do for a merchant name or a total


@dataclass(frozen=True)
class Line:
    text: str = ""
    align: Align = Align.LEFT
    bold: bool = False
    size: Size = Size.NORMAL
    qr_payload: str | None = None  # a QR line carries no text; the payload is encoded instead


@dataclass
class Receipt:
    columns: int
    lines: list[Line] = field(default_factory=list)

    def add(self, text: str = "", **kwargs) -> None:
        self.lines.append(Line(text, **kwargs))

    def two_columns(self, left: str, right: str, **kwargs) -> None:
        """`left` flush left, `right` flush right, padded to the paper width."""
        width = self.columns // (kwargs.get("size", Size.NORMAL).value)
        gap = width - len(left) - len(right)
        if gap < 1:
            gap = 1
        self.lines.append(Line(f"{left}{' ' * gap}{right}", **kwargs))

    def separator(self, char: str = "=") -> None:
        self.lines.append(Line(char * self.columns))

    def qr(self, payload: str) -> None:
        self.lines.append(Line(qr_payload=payload, align=Align.CENTER))

    def text_lines(self) -> list[str]:
        """The receipt as the plain text an ideal OCR would return, one entry per printed line."""
        out = []
        for line in self.lines:
            if line.qr_payload is not None:
                continue
            width = self.columns // line.size.value
            if line.align is Align.CENTER:
                out.append(line.text.center(width).rstrip())
            elif line.align is Align.RIGHT:
                out.append(line.text.rjust(width))
            else:
                out.append(line.text.rstrip())
        return out
