#!/usr/bin/env python

from translate.convert import po2csv
from translate.convert import test_convert
from translate.misc import wStringIO
from translate.storage import po
from translate.storage import csvl10n

class TestPO2CSV:
    def po2csv(self, posource):
        """helper that converts po source to csv source without requiring files"""
        inputfile = wStringIO.StringIO(posource)
        inputpo = po.pofile(inputfile)
        convertor = po2csv.po2csv()
        outputcsv = convertor.convertfile(inputpo)
        return outputcsv

    def singleelement(self, storage):
        """checks that the pofile contains a single non-header element, and returns it"""
        assert len(storage.units) == 1
        return storage.units[0]

    def test_simpleentity(self):
        """checks that a simple csv entry definition converts properly to a po entry"""
        minipo = r'''#: term.cpp
msgid "Term"
msgstr "asdf"'''
        csvfile = self.po2csv(minipo)
        unit = self.singleelement(csvfile)
        assert unit.comment == "term.cpp"
        assert unit.source == "Term"
        assert unit.target == "asdf"

    def test_multiline(self):
        """tests multiline po entries"""
        minipo = r'''msgid "First part "
"and extra"
msgstr "Eerste deel "
"en ekstra"'''
        csvfile = self.po2csv(minipo)
        unit = self.singleelement(csvfile)
        assert unit.source == "First part and extra"
        assert unit.target == "Eerste deel en ekstra"

    def test_escapednewlines(self):
        """Test the escaping of newlines"""
        minipo = r'''msgid "First line\nSecond line"
msgstr "Eerste lyn\nTweede lyn"
'''
        csvfile = self.po2csv(minipo)
        unit = self.singleelement(csvfile)
        assert unit.source == "First line\nSecond line"
        assert unit.target == "Eerste lyn\nTweede lyn"

    def test_escapedtabs(self):
        """Test the escaping of tabs"""
        minipo = r'''msgid "First column\tSecond column"
msgstr "Eerste kolom\tTweede kolom"
'''
        csvfile = self.po2csv(minipo)
        unit = self.singleelement(csvfile)
        assert unit.source == "First column\tSecond column"
        assert unit.target == "Eerste kolom\tTweede kolom"
        assert csvfile.findunit("First column\tSecond column").target == "Eerste kolom\tTweede kolom"

    def test_escapedquotes(self):
        """Test the escaping of quotes (and slash)"""
        minipo = r'''msgid "Hello \"Everyone\""
msgstr "Good day \"All\""

msgid "Use \\\"."
msgstr "Gebruik \\\"."
'''
        csvfile = self.po2csv(minipo)
        assert csvfile.findunit('Hello "Everyone"').target == 'Good day "All"'
        assert csvfile.findunit('Use \\".').target == 'Gebruik \\".'

    def test_singlequotes(self):
        """Tests that single quotes are preserved correctly"""
        minipo = '''msgid "source 'source'"\nmsgstr "target 'target'"\n'''
        csvfile = self.po2csv(minipo)
        print str(csvfile)
        assert csvfile.findunit("source 'source'").target == "target 'target'"
        # Make sure we don't mess with start quotes until writing
        minipo = '''msgid "'source'"\nmsgstr "'target'"\n'''
        csvfile = self.po2csv(minipo)
        print str(csvfile)
        assert csvfile.findunit(r"'source'").target == r"'target'"
        # TODO check that we escape on writing not in the internal representation

    def test_empties(self):
        """Tests that things keep working with empty entries"""
        minipo = 'msgid "Source"\nmsgstr ""\n\nmsgid ""\nmsgstr ""'
        csvfile = self.po2csv(minipo)
        assert csvfile.findunit("Source") is not None
        assert csvfile.findunit("Source").target == ""
        assert len(csvfile.units) == 1

class TestPO2CSVCommand(test_convert.TestConvertCommand, TestPO2CSV):
    """Tests running actual po2csv commands on files"""
    convertmodule = po2csv

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "-P, --pot")
        options = self.help_check(options, "--columnorder=COLUMNORDER", last=True)

