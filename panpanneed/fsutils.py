from __future__ import annotations
from dataclasses import dataclass
import typing


@dataclass(frozen=True)
class File:
    """
    Links to all files are accessed through the 'view' mode.
    """

    secs: str


@dataclass(frozen=True)
class Directory:
    """
    Links to all directories are accessed through the 'download-zip' mode.
    """

    secs: str


if typing.TYPE_CHECKING:
    FsObject = File | Directory
else:
    FsObject = object
