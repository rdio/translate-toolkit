#!/usr/bin/env python

from translate.storage import po
from translate.tools import pogrep
from translate.misc import wStringIO

class TestPOGrep:
    def poparse(self, posource):
        """helper that parses po source without requiring files"""
        dummyfile = wStringIO.StringIO(posource)
        pofile = po.pofile(dummyfile)
        return pofile

    def pogrep(self, posource, searchstring, cmdlineoptions=None):
        """helper that parses po source and passes it through a filter"""
        if cmdlineoptions is None:
            cmdlineoptions = []
        options, args = pogrep.cmdlineparser().parse_args(["xxx.po"] + cmdlineoptions)
        grepfilter = pogrep.pogrepfilter(searchstring, options.searchparts, options.ignorecase, options.useregexp, options.invertmatch, options.accelchar)
        tofile = grepfilter.filterfile(self.poparse(posource))
        print str(tofile)
        return str(tofile)

    def test_simplegrep_msgid(self):
        """grep for a string in the source"""
        posource = '#: test.c\nmsgid "test"\nmsgstr "rest"\n\n'
        poresult = self.pogrep(posource, "test", ["--search=msgid"])
        assert poresult == posource
        poresult = self.pogrep(posource, "rest", ["--search=msgid"])
        assert poresult == ""

    def test_simplegrep_msgstr(self):
        """grep for a string in the target"""
        posource = '#: test.c\nmsgid "test"\nmsgstr "rest"\n\n'
        poresult = self.pogrep(posource, "rest", ["--search=msgstr"])
        assert poresult == posource
        poresult = self.pogrep(posource, "test", ["--search=msgstr"])
        assert poresult == ""

    def test_simplegrep_source(self):
        """grep for a string in the source"""
        posource = '#: test.c\nmsgid "test"\nmsgstr "rest"\n\n'
        poresult = self.pogrep(posource, "test.c", ["--search=source"])
        assert poresult == posource
        poresult = self.pogrep(posource, "rest.c", ["--search=source"])
        assert poresult == ""

    def test_simplegrep_comments(self):
        """grep for a string in the comments"""
        posource = '# (review) comment\n#: test.c\nmsgid "test"\nmsgstr "rest"\n\n'
        poresult = self.pogrep(posource, "review", ["--search=comment"])
        assert poresult == posource
        poresult = self.pogrep(posource, "test", ["--search=comment"])
        assert poresult == ""

    def test_unicode_message_searchstring(self):
        """check that we can grep unicode messages and use unicode search strings"""
        poascii = '# comment\n#: test.c\nmsgid "test"\nmsgstr "rest"\n\n'
        pounicode = '# comment\n#: test.c\nmsgid "test"\nmsgstr "rešṱ"\n\n'
        queryascii = 'rest'
        queryunicode = 'rešṱ'
        for source, search, expected in [(poascii, queryascii, poascii), 
                                         (poascii, queryunicode, ''),
                                         (pounicode, queryascii, ''),
                                         (pounicode, queryunicode, pounicode)]:
          print "Source:\n%s\nSearch: %s\n" % (source, search)
          poresult = self.pogrep(source, search)
          assert poresult == expected
