#!/usr/bin/env python

"""base classes for storage interfaces"""

import pickle

class TranslationUnit:
    def __init__(self, source):
        """Constructs a TranslationUnit containing the given source string"""
        self.source = source
    def __eq__(self, other):
        """Compares two TranslationUnits"""
        return self.source == other.source

class TranslationStore:
    """Base class for stores for multiple translation units of type UnitClass"""
    UnitClass = TranslationUnit

    def __init__(self):
        """Constructs a blank TranslationStore"""
        self.units = []

    def addsourceunit(self, source):
        """Adds and returns a new unit with the given source string"""
        unit = self.UnitClass(source)
        self.units.append(unit)
        return unit

    def findunit(self, source):
        """Finds the unit with the given source string"""
        for unit in self.units:
            if unit.source == source:
                return unit
        raise KeyError("Unit with source string %r not found" % source)

    def __str__(self):
        """Converts to a string representation that can be parsed back using parse"""
        return pickle.dumps(self)

    @classmethod
    def parsestring(cls, storestring):
        """Converts the string representation back to an object"""
        return pickle.loads(storestring)

    def savefile(self, storefile):
        """Writes the string representation to the given file (or filename)"""
        storestring = str(self)
        if isinstance(storefile, basestring):
            storefile = open(storefile, "w")
        storefile.write(storestring)
        storefile.close()

    @classmethod
    def parsefile(cls, storefile):
        """Reads the given file (or opens the given filename) and parses back to an object"""
        if isinstance(storefile, basestring):
            storefile = open(storefile, "r")
        storestring = storefile.read()
        return cls.parsestring(storestring)

