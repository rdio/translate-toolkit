#!/usr/bin/env python

from translate.convert import moz2po
from translate.convert import test_convert
from translate.misc import wStringIO
from translate.storage import po
import sys

class TestMoz2PO:
  pass

class TestMoz2POCommand(test_convert.TestConvertCommand, TestMoz2PO):
    """Tests running actual html2po commands on files"""
    convertmodule = moz2po
    defaultoptions = {"progress": "none"}

    def test_help(self):
        """tests getting help"""
        help_string = test_convert.TestConvertCommand.test_help(self)
        assert "--duplicates" in help_string
