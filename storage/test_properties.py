#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.storage import properties
from translate.misc import wStringIO

class TestProperties:
    def propparse(self, propsource):
        """helper that parses properties source without requiring files"""
        dummyfile = wStringIO.StringIO(propsource)
        propfile = properties.propfile(dummyfile)
        return propfile

    def propregen(self, propsource):
        """helper that converts properties source to propfile object and back"""
        return str(self.propparse(propsource))

    def test_simpledefinition(self):
        """checks that a simple properties definition is parsed correctly"""
        propsource = 'test_me=I can code!'
        propfile = self.propparse(propsource)
        assert len(propfile.propelements) == 1
        propelement = propfile.propelements[0]
        assert propelement.name == "test_me"
        assert propelement.msgid == "I can code!"

    def test_simpledefinition_source(self):
        """checks that a simple properties definition can be regenerated as source"""
        propsource = 'test_me=I can code!'
        propregen = self.propregen(propsource)
        assert propsource + '\n' == propregen

    def test_unicode_escaping(self):
        """check that escapes unicode is converted properly"""
        propsource = "unicode=\u0411\u0416\u0419\u0428"
        propfile = self.propparse(propsource)
        assert len(propfile.propelements) == 1
        propelement = propfile.propelements[0]
        assert propelement.name == "unicode"
        assert propelement.msgid.encode("UTF-8") == "БЖЙШ"

    def test_newlines_startend(self):
        """check that we preserver \n that appear at start and end of properties"""
        propsource = "newlines=\\ntext\\n"
        propregen = self.propregen(propsource)
        assert propsource + '\n' == propregen

    def test_whitespace_removal(self):
        """check that we remove extra whitespace around property"""
        propsource = '''  whitespace  =  Start \n'''
        propfile = self.propparse(propsource)
        propelement = propfile.propelements[0]
        assert propelement.name == "whitespace"
        assert propelement.msgid == "Start "
     
