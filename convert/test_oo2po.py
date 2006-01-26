#!/usr/bin/env python

from translate.convert import oo2po
from translate.misc import wStringIO
from translate.storage import po
from translate.storage import oo

class TestOO2PO:
    def oo2po(self, oosource, sourcelanguage='en-US', targetlanguage='af-ZA'):
        """helper that converts oo source to po source without requiring files"""
        inputoo = oo.oofile(oosource)
        convertor = oo2po.oo2po(sourcelanguage, targetlanguage)
        outputpo = convertor.convertfile(inputoo)
        return outputpo

    def singleelement(self, pofile):
        """checks that the pofile contains a single non-header element, and returns it"""
        assert len(pofile.units) == 2
        assert pofile.units[0].isheader()
        return pofile.units[1]

    def test_simpleentity(self):
        """checks that a simple oo entry converts properly to a po entry"""
	oosource = r'svx	source\dialog\numpages.src	0	string	RID_SVXPAGE_NUM_OPTIONS	STR_BULLET			0	en-US	Character				20050924 09:13:58'
        pofile = self.oo2po(oosource)
        pounit = self.singleelement(pofile)
        assert po.unquotefrompo(pounit.msgid) == "Character"
        assert po.unquotefrompo(pounit.msgstr) == ""

    def test_escapes(self):
        """checks that a simple oo entry converts escapes properly to a po entry"""
	oosource = r"wizards	source\formwizard\dbwizres.src	0	string	RID_DB_FORM_WIZARD_START + 19				0	en-US	The join '<FIELDNAME1>' and '<FIELDNAME2>' has been selected twice.\nBut joins may only be used once.				20050924 09:13:58"
        pofile = self.oo2po(oosource)
        pounit = self.singleelement(pofile)
        poelementsrc = str(pounit)
        assert r"twice.\nBut" in poelementsrc

