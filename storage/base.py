#!/usr/bin/env python

"""base classes for storage interfaces"""

import pickle

class TranslationUnit:
    def __init__(self, source):
        self.source = source
    def __eq__(self, other):
        return self.source == other.source

class TranslationStore:
    UnitClass = TranslationUnit

    def __init__(self):
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
    def parse(cls, savedstore):
        """Converts the string representation back to an object"""
        return pickle.loads(savedstore)

