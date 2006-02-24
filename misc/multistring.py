#!/usr/bin/env python

"""Supports a hybrid Unicode string that can also have a list of alternate strings in the alt attribute"""

from translate.misc import autoencode

class multistring(autoencode.autoencode):
    def __new__(newtype, string=u"", encoding=None, errors=None):
        if isinstance(string, list):
            if not string:
                raise ValueError("multistring must contain at least one string")
            mainstring = string[0]
            newstring = multistring.__new__(newtype, string[0], encoding, errors)
            newstring.alt = [autoencode.autoencode.__new__(autoencode.autoencode, altstring, encoding, errors) for altstring in string[1:]]
        else:
            newstring = autoencode.autoencode.__new__(newtype, string, encoding, errors)
            newstring.alt = []
        return newstring

    def __init__(self, *args, **kwargs):
        super(multistring, self).__init__(*args, **kwargs)
        if not hasattr(self, "alt"):
            self.alt = []    

    def __cmp__(self, otherstring):
        if isinstance(otherstring, multistring):
            parentcompare = autoencode.autoencode.__cmp__(self, otherstring)
            if parentcompare:
                return parentcompare
            else:
                return cmp(self.alt, otherstring.alt)
        elif isinstance(otherstring, autoencode.autoencode):
            return autoencode.autoencode(self).__cmp__(otherstring)
        elif isinstance(otherstring, unicode):
            return unicode(self).__cmp__(otherstring)
        elif isinstance(otherstring, str):
            return cmp(str(self), otherstring)
        else:
            return cmp(type(self), type(otherstring))

    def __repr__(self):
        if not hasattr(self, "alt"):
            print id(self), "has no alt"
            return super(multistring, self).__repr__()
        parts = [autoencode.autoencode.__repr__(self)] + [repr(a) for a in self.alt]
        return "multistring(" + "/".join(parts) + ")"

