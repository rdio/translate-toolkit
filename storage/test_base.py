#!/usr/bin/env python

"""tests for storage base classes"""

from translate.storage import base
from py import test
import os

class TestTranslationUnit:
    """Tests a TranslationUnit.
    Derived classes can reuse these tests by pointing UnitClass to a derived Unit"""
    UnitClass = base.TranslationUnit
    def test_create(self):
        """tests a simple creation with a source string"""
        unit = self.UnitClass("Test String")
        assert unit.source == "Test String"

    def test_eq(self):
        """tests equality comparison"""
        unit1 = self.UnitClass("Test String")
        unit2 = self.UnitClass("Test String")
        unit3 = self.UnitClass("Test String")
        unit4 = self.UnitClass("Blessed String")
        unit5 = self.UnitClass("Blessed String")
        unit6 = self.UnitClass("Blessed String")
        assert unit1 == unit1
        assert unit1 == unit2
        assert unit1 != unit4
        unit1.settarget("Stressed Ting")
        unit2.settarget("Stressed Ting")
        unit5.settarget("Stressed Bling")
        unit6.settarget("Stressed Ting")
        assert unit1 == unit2
        assert unit1 != unit3
        assert unit4 != unit5
        assert unit1 != unit6

    def test_target(self):
        unit = self.UnitClass("Test String")
        assert unit.target is None
        unit.settarget("Stressed Ting")
        assert unit.target == "Stressed Ting"
        unit.settarget("Stressed Bling")
        assert unit.target == "Stressed Bling"

class TestTranslationStore:
    """Tests a TranslationStore.
    Derived classes can reuse these tests by pointing StoreClass to a derived Store"""
    StoreClass = base.TranslationStore

    def setup_method(self, method):
        """Allocates a unique self.filename for the method, making sure it doesn't exist"""
        self.filename = "%s_%s.test" % (self.__class__.__name__, method.__name__)
        if os.path.exists(self.filename):
            os.remove(self.filename)

    def teardown_method(self, method):
        """Makes sure that if self.filename was created by the method, it is cleaned up"""
        if os.path.exists(self.filename):
            os.remove(self.filename)

    def test_create_blank(self):
        """Tests creating a new blank store"""
        store = self.StoreClass()
        assert len(store.units) == 0

    def test_add(self):
        """Tests adding a new unit with a source string"""
        store = self.StoreClass()
        unit = store.addsourceunit("Test String")
        assert len(store.units) == 1
        assert unit.source == "Test String"

    def test_find(self):
        """Tests searching for a given source string"""
        store = self.StoreClass()
        unit1 = store.addsourceunit("Test String")
        unit2 = store.addsourceunit("Blessed String")
        assert store.findunit("Test String") == unit1
        assert store.findunit("Blessed String") == unit2
        assert test.raises(KeyError, store.findunit, ("Nest String",))

    def reparse(self, store):
        """converts the store to a string and back to a store again"""
        storestring = str(store)
        newstore = self.StoreClass.parsestring(storestring)
        return newstore

    def check_equality(self, store1, store2):
        """asserts that store1 and store2 are the same"""
        assert len(store1.units) == len(store2.units)
        for n, unit in enumerate(store2.units):
            assert store2.units[n] == unit

    def test_parse(self):
        """Tests converting to a string and parsing the resulting string"""
        store = self.StoreClass()
        unit1 = store.addsourceunit("Test String")
        unit2 = store.addsourceunit("Blessed String")
        newstore = self.reparse(store)
        self.check_equality(store, newstore)

    def test_files(self):
        """Tests saving to and loading from files"""
        store = self.StoreClass()
        unit1 = store.addsourceunit("Test String")
        unit2 = store.addsourceunit("Blessed String")
        store.savefile(self.filename)
        newstore = self.StoreClass.parsefile(self.filename)
        self.check_equality(store, newstore)

