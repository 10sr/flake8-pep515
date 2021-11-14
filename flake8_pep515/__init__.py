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


def _find_invalid_sep(string: str, len_: int) -> int:
    """Check if number literal is properly separated.

    Returns the position where invalid separator was found, or -1
    if input is separated validly.

    :param string: Input string.
    :param len_: Separation length.
    :returns: Position where invalid separator was found, or -1 for valid input.
    """
    toplevel = True
    current_len = 0
    for i, s in enumerate(string):
        if s == _SEPARATOR:
            if current_len == len_:
                current_len = 0
                continue
            elif current_len < len_ and toplevel:
                toplevel = False
                current_len = 0
                continue
            else:
                return i

        if current_len > len_:
            return i

        current_len += 1

    if current_len != len_:
        return len(string)
    return -1


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

        self._check_for = {
            type_: getattr(self, f"_check_{type_.name}")
            for type_ in _LITERAL_TYPE
        }
        return

    def run(self) -> Iterable[_ERROR]:
        """Run checker.

        :yields: Errors found.
        """
        for token in self.file_tokens:
            if token.type != tokenize.NUMBER:
                continue

            literal_type = _LITERAL_TYPE.of(token.string)

            yield from self._check_for[literal_type](token)
        return

    def _check_DEC(self, token: tokenize.TokenInfo) -> Iterable[_ERROR]:
        invalid = _find_invalid_sep(token.string, self.dec_len)
        if invalid >= 0:
            yield (token.start[0], token.start[1] + invalid, "NSP001 DEC Invalid", None)
        return

    def _check_BIN(self, token: tokenize.TokenInfo) -> Iterable[_ERROR]:
        body = token.string[2:]
        invalid = _find_invalid_sep(body, self.bin_len)
        if invalid >= 0:
            yield (token.start[0], token.start[1] + invalid, "NSP011 BIN Invalid", None)
        return

    def _check_OCT(self, token: tokenize.TokenInfo) -> Iterable[_ERROR]:
        body = token.string[2:]
        invalid = _find_invalid_sep(body, self.oct_len)
        if invalid >= 0:
            yield (token.start[0], token.start[1] + invalid, "NSP021 OCT Invalid", None)
        return

    def _check_HEX(self, token: tokenize.TokenInfo) -> Iterable[_ERROR]:
        body = token.string[2:]
        invalid = _find_invalid_sep(body, self.hex_len)
        if invalid >= 0:
            yield (token.start[0], token.start[1] + invalid, "NSP031 HEX Invalid", None)
        return

    def _check_POINTFLOAT(self, token: tokenize.TokenInfo) -> Iterable[_ERROR]:
        raise NotImplemented

    def _check_EXPONENTFLOAT(self, token: tokenize.TokenInfo) -> Iterable[_ERROR]:
        raise NotImplemented
