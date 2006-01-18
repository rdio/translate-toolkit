#!/usr/bin/env python

from translate.storage import tmx
from translate.misc import wStringIO

class TestTMX:
    def tmxparse(self, tmxsource):
        """helper that parses tmx source without requiring files"""
        dummyfile = wStringIO.StringIO(tmxsource)
        tmxfile = tmx.TmxParser(dummyfile)
        return tmxfile

    def test_translate(self):
        tmxfile= tmx.TmxParser()
        assert tmxfile.translate("Anything") is None
        tmxfile.addtranslation("A string of characters", "en", "'n String karakters", "af")
        assert tmxfile.translate("A string of characters") == "'n String karakters"

    def test_addtranslation(self):
        """tests that addtranslation stores strings correctly"""
        tmxfile = tmx.TmxParser()
        tmxfile.addtranslation("A string of characters", "en", "'n String karakters", "af")
        newfile = self.tmxparse(tmxfile.getxml())
        assert newfile.translate("A string of characters") == "'n String karakters"
