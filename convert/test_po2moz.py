#!/usr/bin/env python

from translate.convert import po2moz
from translate.convert import test_convert
from translate.misc import wStringIO
from translate.storage import po
import sys

class TestPO2Moz:
  pass

class TestPO2MozCommand(test_convert.TestConvertCommand, TestPO2Moz):
    """Tests running actual html2po commands on files"""
    convertmodule = po2moz
    defaultoptions = {"progress": "none"}

    def test_help(self):
        """tests getting help"""
        help_string = test_convert.TestConvertCommand.test_help(self)
        assert "-lLOCALE, --locale=LOCALE" in help_string
        assert "--clonexpi=CLONEXPI" in help_string
        assert "--fuzzy" in help_string
        assert "--nofuzzy" in help_string
