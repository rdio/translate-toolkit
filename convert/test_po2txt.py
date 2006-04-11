#!/usr/bin/env python

from translate.convert import po2txt
from translate.convert import test_convert
from translate.misc import wStringIO
from translate.storage import po
import sys

class TestPO2Txt:
  pass

class TestPO2TxtCommand(test_convert.TestConvertCommand, TestPO2Txt):
    """Tests running actual po2txt commands on files"""
    convertmodule = po2txt
    defaultoptions = {"progress": "none"}

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "-tTEMPLATE, --template=TEMPLATE")
        options = self.help_check(options, "-wWRAP, --wrap=WRAP", last=True)
