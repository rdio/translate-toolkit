#!/usr/bin/env python

from translate.storage import po
from translate.misc import wStringIO

class TestPO:
    def poparse(self, posource):
        """helper that parses po source without requiring files"""
        dummyfile = wStringIO.StringIO(posource)
        pofile = po.pofile(dummyfile)
        return pofile

    def poparse_real(self, posource):
        """helper that creates a real PO file for parsing"""
        file = open("/tmp/joe.po", "w")
        file.write(posource)
	file.close()
        return open("/tmp/joe.po", "r")

    def poregen(self, posource):
        """helper that converts po source to pofile object and back"""
        return str(self.poparse(posource))

    def test_simpleentry(self):
        """checks that a simple po entry is parsed correctly"""
        posource = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        pofile = self.poparse(posource)
        assert len(pofile.poelements) == 1
        thepo = pofile.poelements[0]
        assert thepo.getsources() == ["test.c"]
        assert po.unquotefrompo(thepo.msgid) == "test"
        assert po.unquotefrompo(thepo.msgstr) == "rest"

    def test_combine_msgidcomments(self):
        """checks that we don't get duplicate msgid comments"""
        posource = 'msgid "test me"\nmsgstr ""'
        pofile = self.poparse(posource)
        thepo = pofile.poelements[0]
        thepo.msgidcomments.append('"_: first comment\\n"')
        thepo.msgidcomments.append('"_: second comment\\n"')
        regenposource = str(pofile)
        assert regenposource.count("_:") == 1

    def test_merge_duplicates(self):
        """checks that merging duplicates works"""
        posource = '#: source1\nmsgid "test me"\nmsgstr ""\n\n#: source2\nmsgid "test me"\nmsgstr ""\n'
        pofile = self.poparse(posource)
        assert len(pofile.poelements) == 2
        pofile.removeduplicates("merge")
        assert len(pofile.poelements) == 1
        assert pofile.poelements[0].getsources() == ["source1", "source2"]

    def test_merge_blanks(self):
        """checks that merging adds msgid_comments to blanks"""
        posource = '#: source1\nmsgid ""\nmsgstr ""\n\n#: source2\nmsgid ""\nmsgstr ""\n'
        pofile = self.poparse(posource)
        assert len(pofile.poelements) == 2
        pofile.removeduplicates("merge")
        assert len(pofile.poelements) == 2
        assert po.getunquotedstr(pofile.poelements[0].msgidcomments) == "_: source1\\n"
        assert po.getunquotedstr(pofile.poelements[1].msgidcomments) == "_: source2\\n"

    def test_keep_blanks(self):
        """checks that keeping keeps blanks and doesn't add msgid_comments"""
        posource = '#: source1\nmsgid ""\nmsgstr ""\n\n#: source2\nmsgid ""\nmsgstr ""\n'
        pofile = self.poparse(posource)
        assert len(pofile.poelements) == 2
        pofile.removeduplicates("keep")
        assert len(pofile.poelements) == 2
        # check we don't add msgidcomments
        assert po.getunquotedstr(pofile.poelements[0].msgidcomments) == ""
        assert po.getunquotedstr(pofile.poelements[1].msgidcomments) == ""

    def test_getunquotedstr(self):
        """checks that getunquotedstr works as advertised"""
        assert po.getunquotedstr(['"First line\nSecond line"'], includeescapes=False) == "First line\nSecond line"

    def test_parse_source_string(self):
        posource = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        pofile = self.poparse(posource)
        assert len(pofile.poelements) == 1

    def test_parse_real_file(self):
        posource = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        tempfile = self.poparse_real(posource)
        pofile = po.pofile(tempfile)
        assert len(pofile.poelements) == 1
	tempfile.close()

