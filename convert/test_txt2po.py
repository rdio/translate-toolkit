#!/usr/bin/env python

from translate.convert import txt2po
from translate.convert import test_convert
from translate.misc import wStringIO
from translate.storage import po
import sys

class TestTxt2PO:
  pass

class TestTxt2POCommand(test_convert.TestConvertCommand, TestTxt2PO):
    """Tests running actual txt2po commands on files"""
    convertmodule = txt2po
    defaultoptions = {"progress": "none"}

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "-P, --pot", last=True)
