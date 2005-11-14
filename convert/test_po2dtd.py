#!/usr/bin/env python

from translate.convert import po2dtd
from translate.misc import wStringIO
from translate.storage import po
from translate.storage import dtd

class TestPO2DTD:
    def po2dtd(self, posource):
        """helper that converts po source to dtd source without requiring files"""
        inputfile = wStringIO.StringIO(posource)
        inputpo = po.pofile(inputfile)
        convertor = po2dtd.po2dtd()
        outputdtd = convertor.convertfile(inputpo)
        return outputdtd

    def test_joinlines(self):
        """tests that po lines are joined seamlessly (bug 16)"""
        multilinepo = '''#: pref.menuPath\nmsgid ""\n"<span>Tools &gt; Options</"\n"span>"\nmsgstr ""\n'''
        dtdfile = self.po2dtd(multilinepo)
        dtdsource = "".join(dtdfile.tolines())
        assert "</span>" in dtdsource

