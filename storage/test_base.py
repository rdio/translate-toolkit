#!/usr/bin/env python

"""tests for storage base classes"""

from translate.storage import base
from py import test
import os

class TestTranslationStore:
    TestClass = base.TranslationStore
    def setup_method(self, method):
        self.filename = "%s_%s.test" % (self.__class__.__name__, method.__name__)
        if os.path.exists(self.filename):
            os.remove(self.filename)
    def teardown_method(self, method):
        if os.path.exists(self.filename):
            os.remove(self.filename)
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
    def test_parse(self):
        store = self.TestClass()
        unit1 = store.addsourceunit("Test String")
        unit2 = store.addsourceunit("Blessed String")
        saved_store = str(store)
        newstore = self.TestClass.parsestring(saved_store)
        assert len(newstore.units) == len(store.units)
        for n, unit in enumerate(store.units):
            assert newstore.units[n] == unit
    def test_files(self):
        store = self.TestClass()
        unit1 = store.addsourceunit("Test String")
        unit2 = store.addsourceunit("Blessed String")
        store.savefile(self.filename)
        newstore = self.TestClass.parsefile(self.filename)
        assert len(newstore.units) == len(store.units)
        for n, unit in enumerate(store.units):
            assert newstore.units[n] == unit

