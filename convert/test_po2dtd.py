#!/usr/bin/env python

from translate.convert import po2dtd
from translate.misc import wStringIO
from translate.storage import po
from translate.storage import dtd
from py import test
import warnings

class TestPO2DTD:
    def po2dtd(self, posource):
        """helper that converts po source to dtd source without requiring files"""
        inputfile = wStringIO.StringIO(posource)
        inputpo = po.pofile(inputfile)
        convertor = po2dtd.po2dtd()
        outputdtd = convertor.convertfile(inputpo)
        return outputdtd

    def merge2dtd(self, dtdsource, posource):
        """helper that merges po translations to dtd source without requiring files"""
        inputfile = wStringIO.StringIO(posource)
        inputpo = po.pofile(inputfile)
        templatefile = wStringIO.StringIO(dtdsource)
        templatedtd = dtd.dtdfile(templatefile)
        convertor = po2dtd.redtd(templatedtd)
        outputdtd = convertor.convertfile(inputpo)
        return outputdtd

    def test_joinlines(self):
        """tests that po lines are joined seamlessly (bug 16)"""
        multilinepo = '''#: pref.menuPath\nmsgid ""\n"<span>Tools &gt; Options</"\n"span>"\nmsgstr ""\n'''
        dtdfile = self.po2dtd(multilinepo)
        dtdsource = "".join(dtdfile.tolines())
        assert "</span>" in dtdsource

    def test_escapedstr(self):
        """tests that \n in msgstr is escaped correctly in dtd"""
        multilinepo = '''#: pref.menuPath\nmsgid "Hello\\nEveryone"\nmsgstr "Good day\\nAll"\n'''
        dtdfile = self.po2dtd(multilinepo)
        dtdsource = "".join(dtdfile.tolines())
        assert "Good day\\nAll" in dtdsource

    def test_ampersandwarning(self):
        """tests that proper warnings are given if invalid ampersands occur"""
        simplestring = '''#: simple.warningtest\nmsgid "Simple String"\nmsgstr "Dimpled &Ring"\n'''
        warnings.resetwarnings()
        warnings.simplefilter("error")
        assert test.raises(Warning, po2dtd.removeinvalidamps, "simple.warningtest", "Dimpled &Ring")
        warnings.resetwarnings()

    def test_ampersandfix(self):
        """tests that invalid ampersands are fixed in the dtd"""
        simplestring = '''#: simple.string\nmsgid "Simple String"\nmsgstr "Dimpled &Ring"\n'''
        dtdfile = self.po2dtd(simplestring)
        dtdsource = "".join(dtdfile.tolines())
        assert "Dimpled Ring" in dtdsource

