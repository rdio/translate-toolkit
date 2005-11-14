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

    def test_simpleentity(self):
        dtdsource = '<!ENTITY test.me "bananas for sale">\n'
        pofile = self.dtd2po(dtdsource)
        assert len(pofile.poelements) == 2
        poelement = pofile.poelements[1]
        assert po.unquotefrompo(poelement.msgid) == "bananas for sale"
        assert po.unquotefrompo(poelement.msgstr) == ""

    def test_emptyentity(self):
        dtdsource = '<!ENTITY credit.translation "">\n'
        pofile = self.dtd2po(dtdsource)
        assert len(pofile.poelements) == 2
        poelement = pofile.poelements[1]
        assert po.unquotefrompo(poelement.msgid) == ""
        assert po.unquotefrompo(poelement.msgstr) == ""

