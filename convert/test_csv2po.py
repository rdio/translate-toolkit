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
          templatefile = wStringIO.StringIO(template)
          inputpot = po.pofile(templatefile)
	else:
	  inputpot = None
        convertor = csv2po.csv2po(templatepo=inputpot)
        outputpo = convertor.convertfile(inputcsv)
        return outputpo

    def singleelement(self, storage):
        """checks that the pofile contains a single non-header element, and returns it"""
        assert len(storage.units) == 1
        return storage.units[0]

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

    def test_newlines(self):
        """tests multiline po entries"""
        minicsv = r'''"Random comment
with continuation","Original text","Langdradige teks
wat lank aanhou"
'''
        pofile = self.csv2po(minicsv)
        unit = self.singleelement(pofile)
        assert not unit.sourcecomments == ["#: Random comment\nwith continuation"]
        assert unit.source == "Original text"
        print unit.target
        assert not unit.target == "Langdradige teks\nwat lank aanhou"

    def test_tabs(self):
        """Test the escaping of tabs"""
        minicsv = ',"First column\tSecond column","Twee kolomme gesky met \t"'
        pofile = self.csv2po(minicsv)
        unit = self.singleelement(pofile)
        print unit.source
        assert unit.source == "First column\tSecond column"
        assert not pofile.findunit("First column\tSecond column").target == "Twee kolomme gesky met \\t"

    def test_quotes(self):
        """Test the escaping of quotes (and slash)"""
        minicsv = r''',"Hello ""Everyone""","Good day ""All"""
,"Use \"".","Gebruik \""."'''
        print minicsv
        csvfile = csvl10n.csvfile(wStringIO.StringIO(minicsv))
        print str(csvfile)
        pofile = self.csv2po(minicsv)
        unit = pofile.units[0]
        assert unit.msgid == ['''"Hello \\"Everyone\\""''']
        assert pofile.findunit('Hello "Everyone"').target == 'Good day "All"'
        print str(pofile)
        for unit in pofile.units:
            print unit.source
            print unit.target
            print
#        assert pofile.findunit('Use \\".').target == 'Gebruik \\".'

    def test_empties(self):
        """Tests that things keep working with empty entries"""
        minicsv = ',Source,'
        pofile = self.csv2po(minicsv)
        assert pofile.findunit("Source") is not None
        assert pofile.findunit("Source").target == ""
        assert len(pofile.units) == 1

