#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.storage import factory
from translate.misc import wStringIO

def classname(filename):
    """returns the classname to ease testing"""
    classinstance = factory.getclass(filename)
    return str(classinstance.__name__).lower()

def givefile(filename, content):
    """returns a file dummy object with the given content"""
    file = wStringIO.StringIO(content)
    file.name = filename
    return file

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

    def test_poxliff(self):
        """tests that we indead get a poxliff file, not just a normal one"""
        poxlifffile = givefile("file.xliff", '''<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.1" xmlns="urn:oasis:names:tc:xliff:document:1.1">
<file datatype="po" original="file.po" source-language="en-US"><body><trans-unit approved="no" id="1" restype="x-gettext-domain-header" xml:space="preserve">
<source>MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
</source>
<target>MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
</target>
</trans-unit></body></file></xliff>''')
        
        assert classname(poxlifffile) == "xlifffile"
        xliffobject = factory.getobject(poxlifffile)
        assert xliffobject.__class__.__name__.lower() == "poxlifffile"
