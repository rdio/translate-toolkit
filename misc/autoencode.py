#!/usr/bin/env python

"""Supports a hybrid Unicode string that knows which encoding is preferable, and uses this when converting to a string."""

class autoencode(unicode):
    def __new__(newtype, string=u"", encoding=None, errors=None):
        if isinstance(string, unicode):
            if errors is None:
                newstring = unicode.__new__(newtype, string)
            else:
                newstring = unicode.__new__(newtype, string, errors=errors)
            if encoding is None and isinstance(string, autoencode):
                newstring.encoding = string.encoding
            else:
                newstring.encoding = encoding
        else:
            if errors is None and encoding is None:
                newstring = unicode.__new__(newtype, string)
            elif errors is None:
                newstring = unicode.__new__(newtype, string, encoding)
            elif encoding is None:
                newstring = unicode.__new__(newtype, string, errors)
            else:
                newstring = unicode.__new__(newtype, string, encoding, errors)
            newstring.encoding = encoding
        return newstring

    def join(self, seq):
        return autoencode(super(autoencode, self).join(seq))

    def __str__(self):
        if self.encoding is None:
            return super(autoencode, self).__str__()
        else:
            return self.encode(self.encoding)

