#!/usr/bin/env python

from translate.convert import csv2po
from translate.misc import wStringIO
from translate.storage import po
from translate.storage import csvl10n

class TestCSV2PO:
    def csv2po(self, csvsource, template=None):
        """helper that converts csv source to po source without requiring files"""
        inputfile = wStringIO.StringIO(csvsource)
        inputcsv = csvl10n.csvfile(inputfile)
	if template:
          templatefile = wStringIO.StringIO(csvsource)
          inputpot = po.pofile(templatefile)
	else:
	  inputpot = None
        convertor = csv2po.csv2po(templatepo=inputpot)
        outputpo = convertor.convertfile(inputcsv)
        return outputpo

    def singleelement(self, pofile):
        """checks that the pofile contains a single non-header element, and returns it"""
        assert len(pofile.units) == 1
        return pofile.units[0]

    def test_simpleentity(self):
        """checks that a simple csv entry definition converts properly to a po entry"""
        csvsource = '''source,original,translation
intl.charset.default,ISO-8859-1,UTF-16'''
        pofile = self.csv2po(csvsource)
        pounit = self.singleelement(pofile)
	print dir(pounit)
        assert pounit.sourcecomments == ["#: " + "intl.charset.default" + "\n"]
        assert po.unquotefrompo(pounit.msgid) == "ISO-8859-1"
        assert po.unquotefrompo(pounit.msgstr) == "UTF-16"

    def test_simpleentity_with_template(self):
        """checks that a simple csv entry definition converts properly to a po entry"""
        csvsource = '''source,original,translation
intl.charset.default,ISO-8859-1,UTF-16'''
        potsource = '''#: intl.charset.default
msgid "ISO-8859-1"
msgstr ""
''' 
        pofile = self.csv2po(csvsource, potsource)
        pounit = self.singleelement(pofile)
        assert pounit.sourcecomments == ["#: " + "intl.charset.default" + "\n"]
        assert po.unquotefrompo(pounit.msgid) == "ISO-8859-1"
        assert po.unquotefrompo(pounit.msgstr) == "UTF-16"

