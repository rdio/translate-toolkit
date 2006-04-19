#!/usr/bin/env python

from translate.storage import poxliff
from translate.storage import test_xliff
from translate.misc import wStringIO
from translate.misc.multistring import multistring

from py import test

class TestPOXLIFFUnit(test_xliff.TestXLIFFUnit):
    UnitClass = poxliff.PoXliffUnit
   
    def test_plurals(self):
        """Tests that plurals are handled correctly."""
        unit = self.UnitClass(multistring(["Cow", "Cows"]))
        print type(unit.source)
        print repr(unit.source)
        assert isinstance(unit.source, multistring)
        assert unit.source.strings == ["Cow", "Cows"]
        assert unit.source == "Cow"

        unit.target = ["Koei", "Koeie"]
        assert isinstance(unit.target, multistring)
        assert unit.target.strings == ["Koei", "Koeie"]
        assert unit.target == "Koei"

        unit.target = [u"Sk\u00ear", u"Sk\u00eare"]
        assert isinstance(unit.target, multistring)
        assert unit.target.strings == [u"Sk\u00ear", u"Sk\u00eare"]
        assert unit.target.strings == [u"Sk\u00ear", u"Sk\u00eare"]
        assert unit.target == u"Sk\u00ear"

class TestPOXLIFFfile(test_xliff.TestXLIFFfile):
    StoreClass = poxliff.PoXliffFile
