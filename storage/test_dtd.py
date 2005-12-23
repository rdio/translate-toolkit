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
        return str(dtdfile)

    def dtdregen(self, dtdsource):
        """helper that converts dtd source to dtdfile object and back"""
        return self.dtdsource(self.dtdparse(dtdsource))

    def test_simpleentity(self):
        """checks that a simple dtd entity definition is parsed correctly"""
        dtdsource = '<!ENTITY test.me "bananas for sale">\n'
        dtdfile = self.dtdparse(dtdsource)
        assert len(dtdfile.dtdelements) == 1
        dtdelement = dtdfile.dtdelements[0]
        assert dtdelement.entity == "test.me"
        assert dtdelement.definition == '"bananas for sale"'

    def test_simpleentity_source(self):
        """checks that a simple dtd entity definition can be regenerated as source"""
        dtdsource = '<!ENTITY test.me "bananas for sale">\n'
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen

    def test_hashcomment_source(self):
        """checks that a #expand comment is retained in the source"""
        dtdsource = '#expand <!ENTITY lang.version "__MOZILLA_LOCALE_VERSION__">\n'
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen

    def test_commentclosing(self):
        """tests that comment closes with trailing space aren't duplicated"""
        dtdsource = '<!-- little comment --> \n<!ENTITY pane.title "Notifications">\n'
        dtdregen = self.dtdregen(dtdsource)
        assert dtdsource == dtdregen

