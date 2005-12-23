#!/usr/bin/env python

from translate.storage import po
from translate.filters import pofilter
from translate.filters import checks
from translate.misc import wStringIO

class TestPOFilter:
    def poparse(self, posource):
        """helper that parses po source without requiring files"""
        dummyfile = wStringIO.StringIO(posource)
        pofile = po.pofile(dummyfile)
        return pofile

    def pofilter(self, posource, checkerconfig=None):
        """helper that parses po source and passes it through a filter"""
        options, args = pofilter.cmdlineparser().parse_args(["xxx.po"])
        checkerclasses = [checks.StandardChecker, pofilter.StandardPOChecker]
        if checkerconfig is None:
          checkerconfig = checks.CheckerConfig()
        checkfilter = pofilter.pocheckfilter(options, checkerclasses, checkerconfig)
        tofile = checkfilter.filterfile(self.poparse(posource))
        return str(tofile)

    def test_simplepass(self):
        """checks that an obviously correct string passes"""
        posource = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        pofile = self.pofilter(posource)
        assert not pofile

    def test_simplefail(self):
        """checks that an obviously wrong string fails"""
        posource = '#: test.c\nmsgid "test"\nmsgstr "REST"\n'
        pofile = self.pofilter(posource)
        assert pofile

