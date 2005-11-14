#!/usr/bin/env python

from translate.convert import dtd2po
from translate.misc import wStringIO
from translate.storage import po
from translate.storage import dtd

class TestDTD2PO:
    def dtd2po(self, dtdsource):
        """helper that converts dtd source to po source without requiring files"""
        inputfile = wStringIO.StringIO(dtdsource)
        inputdtd = dtd.dtdfile(inputfile)
        convertor = dtd2po.dtd2po()
        outputpo = convertor.convertfile(inputdtd)
        return outputpo

    def singleelement(self, pofile):
        """checks that the pofile contains a single non-header element, and returns it"""
        assert len(pofile.poelements) == 2
        assert pofile.poelements[0].isheader()
        return pofile.poelements[1]

    def test_simpleentity(self):
        """checks that a simple dtd entity definition converts properly to a po entry"""
        dtdsource = '<!ENTITY test.me "bananas for sale">\n'
        pofile = self.dtd2po(dtdsource)
        poelement = self.singleelement(pofile)
        assert po.unquotefrompo(poelement.msgid) == "bananas for sale"
        assert po.unquotefrompo(poelement.msgstr) == ""

    def test_emptyentity(self):
        """bug 15 - checks that empty entity definitions survive into po file"""
        dtdsource = '<!ENTITY credit.translation "">\n'
        pofile = self.dtd2po(dtdsource)
        poelement = self.singleelement(pofile)
        assert "credit.translation" in "".join(poelement.tolines())

    def test_entitynameincomment(self):
        """bug 30 - error converting original dtd entity """
        dtdsource = '<!--LOCALIZATION NOTE (editorCheck.label):\nDONT_TRANSLATE -->\n' + \
            '<!ENTITY editorCheck.label "Composer">\n<!ENTITY editorCheck.accesskey "c">\n'
        pofile = self.dtd2po(dtdsource)
        poelement = self.singleelement(pofile)
        assert '# DONT_TRANSLATE\n' in poelement.othercomments

