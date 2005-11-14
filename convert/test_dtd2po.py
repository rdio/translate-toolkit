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

    def test_kdecomment_merge(self):
        """test that LOCALIZATION NOTES are added properly as KDE comments and merged with duplicate comments"""
        dtdtemplate = '<!--LOCALIZATION NOTE (%s): Edit box appears beside this label -->\n' + \
            '<!ENTITY %s "If publishing to a FTP site, enter the HTTP address to browse to:">\n'
        dtdsource = dtdtemplate % ("note1.label", "note1.label") + dtdtemplate % ("note2.label", "note2.label")
        pofile = self.dtd2po(dtdsource)
        pofile.poelements = pofile.poelements[1:]
        posource = ''.join(pofile.tolines())
        print posource
        assert posource.count('"_:') <= len(pofile.poelements)

    def test_donttranslate_label(self):
        """bug 30 - strangeness when label entity is marked DONT_TRANSLATE and accesskey is not"""
        dtdsource = '<!--LOCALIZATION NOTE (editorCheck.label): DONT_TRANSLATE -->\n' + \
            '<!ENTITY editorCheck.label "Composer">\n<!ENTITY editorCheck.accesskey "c">\n'
        pofile = self.dtd2po(dtdsource)
        posource = ''.join(pofile.tolines())
        # we need to decided what we're going to do here - see the comments in bug 30
        # this tests the current implementation which is that the DONT_TRANSLATE string is removed, but the other remains
        assert 'editorCheck.label' not in posource
        assert 'editorCheck.accesskey' in posource

