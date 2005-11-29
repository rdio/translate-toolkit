#!/usr/bin/env python

from translate.storage import po
from translate.misc import wStringIO

class TestPO:
    def poparse(self, posource):
        """helper that parses po source without requiring files"""
        dummyfile = wStringIO.StringIO(posource)
        pofile = po.pofile(dummyfile)
        return pofile

    def posource(self, pofile):
        """helper that converts a po file back to source code"""
        return "".join(pofile.tolines())

    def poregen(self, posource):
        """helper that converts po source to pofile object and back"""
        return self.posource(self.poparse(posource))

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
        regenposource = self.posource(pofile)
        assert regenposource.count("_:") == 1

