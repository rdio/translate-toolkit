#!/usr/bin/env python

"""base classes for storage interfaces"""

import pickle

def force_override(method, baseclass):
    """forces derived classes to override method"""
    if type(method.im_self) == type(baseclass):
        # then this is a classmethod and im_self is the actual class
        actualclass = method.im_self
    else:
        actualclass = method.im_class
    if actualclass != baseclass:
        raise NotImplementedError("%s does not reimplement %s as required by %s" % (actualclass.__name__, method.__name__, baseclass.__name__))

class TranslationUnit:
    def __init__(self, source):
        """Constructs a TranslationUnit containing the given source string"""
        self.source = source
        self.target = None

    def __eq__(self, other):
        """Compares two TranslationUnits"""
        return self.source == other.source and self.target == other.target

    def settarget(self, target):
        """Sets the target string to the given value"""
        self.target = target

class TranslationStore(object):
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
        force_override(self.__str__, TranslationStore)
        return pickle.dumps(self)

    def parsestring(cls, storestring):
        """Converts the string representation back to an object"""
        force_override(cls.parsestring, TranslationStore)
        return pickle.loads(storestring)
    parsestring = classmethod(parsestring)

    def savefile(self, storefile):
        """Writes the string representation to the given file (or filename)"""
        storestring = str(self)
        if isinstance(storefile, basestring):
            storefile = open(storefile, "w")
        storefile.write(storestring)
        storefile.close()

    def parsefile(cls, storefile):
        """Reads the given file (or opens the given filename) and parses back to an object"""
        if isinstance(storefile, basestring):
            storefile = open(storefile, "r")
        storestring = storefile.read()
        return cls.parsestring(storestring)
    parsefile = classmethod(parsefile)

