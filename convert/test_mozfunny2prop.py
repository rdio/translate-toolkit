#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.convert import mozfunny2prop
from translate.misc import wStringIO
from translate.storage import po

class TestInc2PO:
    def inc2po(self, propsource, proptemplate=None):
        """helper that converts .inc source to po source without requiring files"""
        inputfile = wStringIO.StringIO(propsource)
        if proptemplate:
          templatefile = wStringIO.StringIO(proptemplate)
        else:
          templatefile = None
        outputfile = wStringIO.StringIO()
        result = mozfunny2prop.inc2po(inputfile, outputfile, templatefile)
        outputpo = outputfile.getvalue()
        outputpofile = po.pofile(wStringIO.StringIO(outputpo))
        return outputpofile

    def singleelement(self, pofile):
        """checks that the pofile contains a single non-header element, and returns it"""
        assert len(pofile.units) == 2
        assert pofile.units[0].isheader()
        print pofile
        return pofile.units[1]

    def countelements(self, pofile):
        """counts the number of non-header entries"""
        assert pofile.units[0].isheader()
        print pofile
        return len(pofile.units) - 1

    def test_simpleentry(self):
        """checks that a simple inc entry converts properly to a po entry"""
        propsource = '#define MOZ_LANGPACK_CREATOR mozilla.org\n'
        pofile = self.inc2po(propsource)
        pounit = self.singleelement(pofile)
        assert pounit.getlocations() == ["MOZ_LANGPACK_CREATOR"]
        assert pounit.source == "mozilla.org"
        assert pounit.target == ""

