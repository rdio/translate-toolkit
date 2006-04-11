#!/usr/bin/env python

from translate.convert import ts2po
from translate.convert import test_convert
from translate.misc import wStringIO
from translate.storage import po
from translate.storage import ts

class TestTS2PO:
    pass

class TestTS2POCommand(test_convert.TestConvertCommand, TestTS2PO):
    """Tests running actual ts2po commands on files"""
    convertmodule = ts2po

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "-P, --pot", last=True)
