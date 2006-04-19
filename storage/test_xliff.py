#!/usr/bin/env python

from translate.storage import xliff2 as xliff
from translate.storage import test_base
from translate.misc import wStringIO
from translate.misc.multistring import multistring

from py import test

class TestXLIFFUnit(test_base.TestTranslationUnit):
    UnitClass = xliff.xliffunit
   
#    def test_plurals(self):
#        """Tests that plurals are handled correctly."""
#        unit = self.UnitClass(multistring(["Cow", "Cows"]))
#        assert isinstance(unit.source, multistring)
#        assert unit.source.strings == ["Cow", "Cows"]
#        assert unit.source == "Cow"

#        unit.target = ["Koei", "Koeie"]
#        assert isinstance(unit.target, multistring)
#        assert unit.target.strings == ["Koei", "Koeie"]
#        assert unit.target == "Koei"

#        unit.target = [u"Sk\u00ear", u"Sk\u00eare"]
#        assert isinstance(unit.target, multistring)
#        assert unit.target.strings == [u"Sk\u00ear", u"Sk\u00eare"]
#        assert unit.target.strings == [u"Sk\u00ear", u"Sk\u00eare"]
#        assert unit.target == u"Sk\u00ear"

class TestXLIFFfile(test_base.TestTranslationStore):
        StoreClass = xliff.xlifffile
        def test_basic(self):
                xlifffile = xliff.xlifffile()
                assert xlifffile.units == []
                xlifffile.addsourceunit("Bla")
                assert len(xlifffile.units) == 1
                newfile = xliff.xlifffile.parsestring(str(xlifffile))
                print str(xlifffile)
                assert len(newfile.units) == 1
                assert newfile.units[0].source == "Bla"
                assert newfile.findunit("Bla").source == "Bla"
                assert newfile.findunit("dit") is None

        def test_source(self):
                xlifffile = xliff.xlifffile()
                xliffunit = xlifffile.addsourceunit("Concept")
                xliffunit.source = "Term"
                newfile = xliff.xlifffile.parsestring(str(xlifffile))
                print str(xlifffile)
                assert newfile.findunit("Concept") is None
                assert newfile.findunit("Term") is not None
        
        def test_target(self):
                xlifffile = xliff.xlifffile()
                xliffunit = xlifffile.addsourceunit("Concept")
                xliffunit.target = "Konsep"
                newfile = xliff.xlifffile.parsestring(str(xlifffile))
                print str(xlifffile)
                assert newfile.findunit("Concept").target == "Konsep"

        def test_sourcelanguage(self):
                xlifffile = xliff.xlifffile(sourcelanguage="xh")
                xmltext = str(xlifffile)
                print xmltext
                assert xmltext.find('source-language="xh"')> 0  
                #TODO: test that it also works for new files.
                
        def test_notes(self):
                xlifffile = xliff.xlifffile()
                unit = xlifffile.addsourceunit("Concept")
                unit.addnote("Please buy bread")
                assert unit.getnotes() == "Please buy bread"
                notenodes = unit.xmlelement.getElementsByTagName("note")
                assert len(notenodes) == 1

                unit.addnote("Please buy milk", origin="Mom")
                notenodes = unit.xmlelement.getElementsByTagName("note")
                assert len(notenodes) == 2
                assert not notenodes[0].hasAttribute("from")
                assert notenodes[1].getAttribute("from") == "Mom"

        def test_fuzzy(self):
                xlifffile = xliff.xlifffile()
                unit = xlifffile.addsourceunit("Concept")
                unit.markfuzzy()
                assert not unit.isfuzzy() #No target yet
                unit.target = "Konsep"
                assert not unit.isfuzzy()
                unit.markfuzzy()
                assert unit.isfuzzy()
                unit.markfuzzy(False)
                assert not unit.isfuzzy()
                unit.markfuzzy(True)
                assert unit.isfuzzy()

#class TestXLIFFfile(test_base.TestTranslationStore):
#    StoreClass = xliff.xlifffile

#    def xliffparse(self, xliffsource):
#        """helper that parses xliff source without requiring files"""
#        dummyfile = wStringIO.StringIO(xliffsource)
#        print xliffsource
#        xlifffile = xliff.xlifffile(dummyfile)
#        return xlifffile

#    def test_translate(self):
#        xlifffile= xliff.xlifffile()
#        assert xlifffile.translate("Anything") is None
#        xlifffile.addtranslation("A string of characters", "en", "'n String karakters", "af")
#        assert xlifffile.translate("A string of characters") == "'n String karakters"

#    def test_addtranslation(self):
#        """tests that addtranslation() stores strings correctly"""
#        xlifffile = xliff.xlifffile()
#        xlifffile.addtranslation("A string of characters", "en", "'n String karakters", "af")
#        newfile = self.xliffparse(str(xlifffile))
#        print str(xlifffile)
#        assert newfile.translate("A string of characters") == "'n String karakters"

#    def test_withnewlines(self):
#        """test addtranslation() with newlines"""
#        xlifffile = xliff.xlifffile()
#        xlifffile.addtranslation("First line\nSecond line", "en", "Eerste lyn\nTweede lyn", "af")
#        newfile = self.xliffparse(str(xlifffile))
#        print str(xlifffile)
#        assert newfile.translate("First line\nSecond line") == "Eerste lyn\nTweede lyn"

#    def test_xmlentities(self):
#        """Test that the xml entities '&' and '<'  are escaped correctly"""
#        xlifffile = xliff.xlifffile()
#        xlifffile.addtranslation("Mail & News", "en", "Nuus & pos", "af")
#        xlifffile.addtranslation("Five < ten", "en", "Vyf < tien", "af")
#        xmltext = str(xlifffile)
#        print "The generated xml:"
#        print xmltext
#        assert xlifffile.translate('Mail & News') == 'Nuus & pos'
#        assert xmltext.index('Mail &amp; News')
#        assert xmltext.find('Mail & News') == -1
#        assert xlifffile.translate('Five < ten') == 'Vyf < tien'
#        assert xmltext.index('Five &lt; ten')
#        assert xmltext.find('Five < ten') == -1

