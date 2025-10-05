# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, Geoffrey M. Poore
# All rights reserved.
#
# Licensed under the BSD 3-Clause License:
# http://opensource.org/licenses/BSD-3-Clause
#

"""
Main QTI package generator - now using QTI 2.1 format.

For backward compatibility with QTI 1.2, the old implementation
is preserved in qti12.py.
"""

import io
import pathlib
from typing import BinaryIO, Union

from .qti30_package import QTI30
from .quiz import Quiz


class QTI(object):
    '''
    Create QTI 3.0 package from a Quiz object.

    This is the main entry point for generating QTI packages from text2qti.
    As of this version, it generates QTI 3.0 format by default.
    '''
    def __init__(self, quiz: Quiz):
        # Delegate to QTI 3.0 implementation
        self._qti30 = QTI30(quiz)
        self.quiz = quiz

    def write(self, bytes_stream: BinaryIO):
        """Write the QTI package to a binary stream."""
        self._qti30.write(bytes_stream)

    def zip_bytes(self) -> bytes:
        """Get the QTI package as bytes."""
        return self._qti30.zip_bytes()

    def save(self, qti_path: Union[str, pathlib.Path]):
        """Save the QTI package to a file."""
        self._qti30.save(qti_path)
