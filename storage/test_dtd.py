#!/usr/bin/env python

from translate.storage import dtd
from translate.misc import wStringIO

class TestDTD:
    def dtdparse(self, dtdsource):
        """helper that parses dtd source without requiring files"""
        dummyfile = wStringIO.StringIO(dtdsource)
        dtdfile = dtd.dtdfile(dummyfile)
        return dtdfile

    def dtdsource(self, dtdfile):
        """helper that converts a dtd file back to source code"""
        return "".join(dtdfile.tolines())

    def test_simpleentity(self):
        """checks that a simple dtd entity definition converts properly to a po entry"""
        dtdsource = '<!ENTITY test.me "bananas for sale">\n'
        dtdfile = self.dtdparse(dtdsource)
        assert len(dtdfile.dtdelements) == 1
        dtdelement = dtdfile.dtdelements[0]
        assert dtdelement.entity == "test.me"
        assert dtdelement.definition == '"bananas for sale"'

