#!/usr/bin/env python

"""tests for storage base classes"""

from py import test
from translate.storage import base

class TestTranslationStore:
    TestClass = base.TranslationStore
    def test_create_blank(self):
        store = self.TestClass()
        assert len(store.units) == 0
    def test_add(self):
        store = self.TestClass()
        unit = store.addsourceunit("Test String")
        assert len(store.units) == 1
        assert unit.source == "Test String"
    def test_find(self):
        store = self.TestClass()
        unit1 = store.addsourceunit("Test String")
        unit2 = store.addsourceunit("Blessed String")
        assert store.findunit("Test String") == unit1
        assert store.findunit("Blessed String") == unit2
        assert test.raises(KeyError, store.findunit, ("Nest String",))
    def test_save(self):
        store = self.TestClass()
        unit1 = store.addsourceunit("Test String")
        unit2 = store.addsourceunit("Blessed String")
        saved_store = str(store)
        newstore = self.TestClass.parse(saved_store)
        assert len(newstore.units) == len(store.units)
        for n, unit in enumerate(store.units):
            assert newstore.units[n] == unit

