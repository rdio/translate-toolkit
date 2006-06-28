#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.storage import factory

def classname(filename):
    """returns the classname to ease testing"""
    classinstance = factory.getclass(filename)
    return str(classinstance.__name__).lower()

class Test_Factory:
    def test_getclass(self):
        assert classname("file.po") == "pofile"
        assert classname("file.pot") == "pofile"
        assert classname("file.dtd.po") == "pofile"

        assert classname("file.tmx") == "tmxfile"
        assert classname("file.af.tmx") == "tmxfile"
        assert classname("file.tbx") == "tbxfile"
        assert classname("file.po.xliff") == "xlifffile"

        assert not classname("file.po") == "tmxfile"
        assert not classname("file.po") == "xlifffile"

