#!/usr/bin/env python

from translate.storage import po
from translate.storage import test_base
from translate.misc import wStringIO

class TestPOUnit(test_base.TestTranslationUnit):
    UnitClass = po.pounit

class TestPO(test_base.TestTranslationStore):
    StoreClass = po.pofile
    def poparse(self, posource):
        """helper that parses po source without requiring files"""
        dummyfile = wStringIO.StringIO(posource)
        pofile = po.pofile(dummyfile)
        return pofile

    def poregen(self, posource):
        """helper that converts po source to pofile object and back"""
        return str(self.poparse(posource))

    def test_simpleentry(self):
        """checks that a simple po entry is parsed correctly"""
        posource = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        pofile = self.poparse(posource)
        assert len(pofile.units) == 1
        thepo = pofile.units[0]
        assert thepo.getsources() == ["test.c"]
        assert thepo.source == "test"
        assert thepo.target == "rest"

    def test_combine_msgidcomments(self):
        """checks that we don't get duplicate msgid comments"""
        posource = 'msgid "test me"\nmsgstr ""'
        pofile = self.poparse(posource)
        thepo = pofile.units[0]
        thepo.msgidcomments.append('"_: first comment\\n"')
        thepo.msgidcomments.append('"_: second comment\\n"')
        regenposource = str(pofile)
        assert regenposource.count("_:") == 1

    def test_merge_duplicates(self):
        """checks that merging duplicates works"""
        posource = '#: source1\nmsgid "test me"\nmsgstr ""\n\n#: source2\nmsgid "test me"\nmsgstr ""\n'
        pofile = self.poparse(posource)
        assert len(pofile.units) == 2
        pofile.removeduplicates("merge")
        assert len(pofile.units) == 1
        assert pofile.units[0].getsources() == ["source1", "source2"]

    def test_merge_blanks(self):
        """checks that merging adds msgid_comments to blanks"""
        posource = '#: source1\nmsgid ""\nmsgstr ""\n\n#: source2\nmsgid ""\nmsgstr ""\n'
        pofile = self.poparse(posource)
        assert len(pofile.units) == 2
        pofile.removeduplicates("merge")
        assert len(pofile.units) == 2
        assert po.getunquotedstr(pofile.units[0].msgidcomments) == "_: source1\\n"
        assert po.getunquotedstr(pofile.units[1].msgidcomments) == "_: source2\\n"

    def test_keep_blanks(self):
        """checks that keeping keeps blanks and doesn't add msgid_comments"""
        posource = '#: source1\nmsgid ""\nmsgstr ""\n\n#: source2\nmsgid ""\nmsgstr ""\n'
        pofile = self.poparse(posource)
        assert len(pofile.units) == 2
        pofile.removeduplicates("keep")
        assert len(pofile.units) == 2
        # check we don't add msgidcomments
        assert po.getunquotedstr(pofile.units[0].msgidcomments) == ""
        assert po.getunquotedstr(pofile.units[1].msgidcomments) == ""

    def test_getunquotedstr(self):
        """checks that getunquotedstr works as advertised"""
        assert po.getunquotedstr(['"First line\nSecond line"'], includeescapes=False) == "First line\nSecond line"
        #XXX:Failing:assert po.getunquotedstr(['"Use \\n."'], includeescapes=False) == "Use \\n."

    def test_parse_source_string(self):
        """parse a string"""
        posource = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        pofile = po.pofile(posource)
        assert len(pofile.units) == 1

    def test_parse_file(self):
        """test parsing a real file"""
        posource = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        pofile = self.poparse(posource)
        assert len(pofile.units) == 1

    def test_unicode(self):
        """check that the po class can handle Unicode characters"""
        posource = 'msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n\n#: test.c\nmsgid "test"\nmsgstr "rest\xe2\x80\xa6"\n'
        pofile = self.poparse(posource)
        print pofile
        assert len(pofile.units) == 2

