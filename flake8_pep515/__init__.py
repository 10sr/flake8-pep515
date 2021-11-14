"""Flake8 plugin that forbids implicit str/bytes literal concatenations."""

from __future__ import annotations

import ast
import enum
import sys
import tokenize

from typing import Iterable
from typing import Tuple


from ._version import __version__

_ERROR = Tuple[int, int, str, None]

_SEPARATOR = "_"


class _LITERAL_TYPE(enum.Enum):
    DEC = enum.auto()
    BIN = enum.auto()
    OCT = enum.auto()
    HEX = enum.auto()
    POINTFLOAT = enum.auto()
    EXPONENTFLOAT = enum.auto()

    @classmethod
    def of(cls, string) -> _LITERAL_TYPE:
        prefix = string[:2].lower()
        if prefix == "0b":
            return cls.BIN
        elif prefix == "0o":
            return cls.OCT
        elif prefix == "0x":
            return cls.HEX
        elif "e" in string.lower():
            return cls.EXPONENTFLOAT
        elif "." in string:
            return cls.POINTFLOAT
        return cls.DEC


def _is_separated_validly(string: str, len_: int) -> bool:
    splitted = string.split(_SEPARATOR)
    first = splitted.pop(0)
    if len(first) > len_:
        return False
    for seg in splitted:
        if len(seg) != len_:
            return False
    return True


class Checker:
    """NSP Checker definition."""

    name = "pep515"
    version = __version__

    dec_len = 3
    bin_len = 4
    oct_len = 4
    hex_len = 4
    point_len = 3
    exponent_len = 3

    def __init__(self, tree: ast.AST, file_tokens: Iterable[tokenize.TokenInfo]):
        """Intialize Checker.

        :param tree: File AST
        :param file_tokens: File tokens
        """
        self.tree = tree
        self.file_tokens = file_tokens
        return

    def _get_check_for(self, type_: _LITERAL_TYPE):
        name_lower = type_.name.lower()
        return getattr(self, f"_check_{name_lower}")

    def run(self) -> Iterable[_ERROR]:
        """Run checker.

        :yields: Errors found.
        """
        for token in self.file_tokens:
            if token.type != tokenize.NUMBER:
                continue

            literal_type = _LITERAL_TYPE.of(token.string)

            yield from self._get_check_for(literal_type)(token)
        return

    def _check_dec(self, token: tokenize.TokenInfo) -> Iterable[_ERROR]:
        if not _is_separated_validly(token.string, self.dec_len):
            yield (token.end[0], token.end[1], "NSP Invalid", None)
        return
        
        
