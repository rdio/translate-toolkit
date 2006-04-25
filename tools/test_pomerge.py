#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.tools import pomerge
from translate.storage import po
from translate.misc import wStringIO

class TestPOMerge:
    def mergepo(self, templatesource, inputsource):
        """merges the sources of the given po files and returns a new po file object"""
        templatefile = wStringIO.StringIO(templatesource)
        inputfile = wStringIO.StringIO(inputsource)
        outputfile = wStringIO.StringIO()
        assert pomerge.mergepo(inputfile, outputfile, templatefile)
        outputpostring = outputfile.getvalue()
        outputpofile = po.pofile(outputpostring)
        return outputpofile

    def countunits(self, pofile):
        """returns the number of non-header items"""
        if pofile.units[0].isheader():
          return len(pofile.units) - 1
        else:
          return len(pofile.units)

    def singleunit(self, pofile):
        """checks that the pofile contains a single non-header unit, and returns it"""
        assert self.countunits(pofile) == 1
        return pofile.units[-1]

    def test_simplemerge(self):
        """checks that a simple po entry merges OK"""
        templatepo = '''#: simple.test\nmsgid "Simple String"\nmsgstr ""\n'''
        inputpo = '''#: simple.test\nmsgid "Simple String"\nmsgstr "Dimpled Ring"\n'''
        pofile = self.mergepo(templatepo, inputpo)
        pounit = self.singleunit(pofile)
        assert po.unquotefrompo(pounit.msgid) == "Simple String"
        assert po.unquotefrompo(pounit.msgstr) == "Dimpled Ring"

    def test_replacemerge(self):
        """checks that a simple po entry merges OK"""
        templatepo = '''#: simple.test\nmsgid "Simple String"\nmsgstr "Dimpled Ring"\n'''
        inputpo = '''#: simple.test\nmsgid "Simple String"\nmsgstr "Dimpled King"\n'''
        pofile = self.mergepo(templatepo, inputpo)
        pounit = self.singleunit(pofile)
        assert po.unquotefrompo(pounit.msgid) == "Simple String"
        assert po.unquotefrompo(pounit.msgstr) == "Dimpled King"

    def test_reflowed_source_comments(self):
        """ensure that we don't duplicate source comments (locations) if they have been reflowed"""
        templatepo = '''#: newMenu.label\n#: newMenu.accesskey\nmsgid "&New"\nmsgstr ""\n'''
        newpo = '''#: newMenu.label newMenu.accesskey\nmsgid "&New"\nmsgstr "&Nuwe"\n'''
        expectedpo = '''#: newMenu.label\n#: newMenu.accesskey\nmsgid "&New"\nmsgstr "&Nuwe"\n\n'''
        pofile = self.mergepo(templatepo, newpo)
        pounit = self.singleunit(pofile)
        print pofile
        assert pofile.getoutput() == expectedpo

    def test_merge_dont_delete_unassociated_comments(self):
        """ensure that we do not delete comments in the PO file that are not assocaited with a message block"""
        templatepo = '''# Lonely comment\n\n# Translation comment\nmsgid "Bob"\nmsgstr "Toolmaker"\n'''
        mergepo = '''# Translation comment\nmsgid "Bob"\nmsgstr "Builder"\n'''
        expectedpo = '''# Lonely comment\n\n# Translation comment\nmsgid "Bob"\nmsgstr "Builder"\n'''
        pofile = self.mergepo(templatepo, mergepo)
        pounit = self.singleunit(pofile)
        print pofile
        assert pofile.getoutput() == expectedpo

    def test_preserve_format(self):
        """Tests that the layout of the po doesn't change unnecessarily"""
        templatepo = '''msgid "First part\\nSecond part"\nmsgstr ""\n"Eerste deel\\nTweede deel"\n\n'''
        mergepo = '''msgid "First part\\n"\n"Second part"\nmsgstr ""\n"Eerste deel\\n"\n"Tweede deel"'''
        pofile = self.mergepo(templatepo, mergepo)
        assert str(pofile) == templatepo

        templatepo = '''msgid "Use a scissor"\nmsgstr "Gebruik 'n sker "\n"om dit te doen"\n'''
        mergepo = '''msgid "Use a scissor"\nmsgstr "Gebruik 'n skêr om dit te doen"\n'''
        expectedpo = '''msgid "Use a scissor"\nmsgstr "Gebruik 'n skêr "\n"om dit te doen"\n\n'''
        pofile = self.mergepo(templatepo, mergepo)
        assert str(pofile) == expectedpo

        templatepo = '''msgid "To do it, use a scissor, please."\nmsgstr "Om dit te doen, "\n"gebruik 'n sker, "\n"asseblief."\n'''
        mergepo = '''msgid "To do it, use a scissor, please."\nmsgstr "Om dit te doen, gebruik 'n skêr, asseblief."\n'''
        expectedpo = '''msgid "To do it, use a scissor, please."\nmsgstr "Om dit te doen, "\n"gebruik 'n skêr, "\n"asseblief."\n\n'''
        pofile = self.mergepo(templatepo, mergepo)
        assert str(pofile) == expectedpo
        mergepo = '''msgid "To do it, use a scissor, please."\nmsgstr "Om dit te doen, gebruik 'n skêr, "\n"asseblief."\n'''
        pofile = self.mergepo(templatepo, mergepo)
        assert str(pofile) == expectedpo
        mergepo = '''msgid "To do it, use a scissor, please."\nmsgstr ""\n"Om dit te doen, "\n"gebruik 'n skêr, asseblief."\n'''
        pofile = self.mergepo(templatepo, mergepo)
        assert str(pofile) == expectedpo

        mergepo = '''msgid ""\n"To do it, use a scissor, "\n"please."\nmsgstr ""\n"Om dit te doen, "\n"gebruik 'n skêr, asseblief."\n'''
        pofile = self.mergepo(templatepo, mergepo)
        assert str(pofile) == expectedpo

        templatepo = '''msgid "To do it, use a scissor, please."\nmsgstr ""\n"Om dit te doen, "\n"gebruik 'n sker, "\n"asseblief."\n'''
        mergepo = '''msgid "To do it, use a scissor, please."\nmsgstr "Om dit te doen, gebruik 'n skêr, asseblief."\n'''
        expectedpo = '''msgid "To do it, use a scissor, please."\nmsgstr ""\n"Om dit te doen, "\n"gebruik 'n skêr, "\n"asseblief."\n\n'''
        pofile = self.mergepo(templatepo, mergepo)
        assert str(pofile) == expectedpo
