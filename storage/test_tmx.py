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
        """tests that addtranslation() stores strings correctly"""
        tmxfile = tmx.TmxParser()
        tmxfile.addtranslation("A string of characters", "en", "'n String karakters", "af")
        newfile = self.tmxparse(tmxfile.getxml())
        print tmxfile.getxml()
        assert newfile.translate("A string of characters") == "'n String karakters"

    def test_withnewlines(self):
        """test addtranslation() with newlines"""
        tmxfile = tmx.TmxParser()
        tmxfile.addtranslation("First line\nSecond line", "en", "Eerste lyn\nTweede lyn", "af")
        newfile = self.tmxparse(tmxfile.getxml())
        print tmxfile.getxml()
        assert newfile.translate("First line\nSecond line") == "Eerste lyn\nTweede lyn"

    def test_xmlentities(self):
        """Test that the xml entities '&' and '<'  are escaped correctly"""
        tmxfile = tmx.TmxParser()
        tmxfile.addtranslation("Mail & News", "en", "Nuus & pos", "af")
        tmxfile.addtranslation("Five < ten", "en", "Vyf < tien", "af")
        xmltext = tmxfile.getxml()
        print "The generated xml:"
        print xmltext
        assert tmxfile.translate('Mail & News') == 'Nuus & pos'
        assert xmltext.index('Mail &amp; News')
        assert xmltext.find('Mail & News') == -1
        assert tmxfile.translate('Five < ten') == 'Vyf < tien'
        assert xmltext.index('Five &lt; ten')
        assert xmltext.find('Five < ten') == -1

