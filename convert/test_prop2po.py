#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.convert import prop2po
from translate.misc import wStringIO
from translate.storage import po
from translate.storage import properties

class TestProp2PO:
    def prop2po(self, propsource):
        """helper that converts .properties source to po source without requiring files"""
        inputfile = wStringIO.StringIO(propsource)
        inputprop = properties.propfile(inputfile)
        convertor = prop2po.prop2po()
        outputpo = convertor.convertfile(inputprop)
        return outputpo

    def singleelement(self, pofile):
        """checks that the pofile contains a single non-header element, and returns it"""
        assert len(pofile.poelements) == 2
        assert pofile.poelements[0].isheader()
        return pofile.poelements[1]

    def test_simpleentry(self):
        """checks that a simple properties entry converts properly to a po entry"""
        propsource = 'SAVEENTRY=Save file\n'
        pofile = self.prop2po(propsource)
        poelement = self.singleelement(pofile)
        assert po.unquotefrompo(poelement.msgid) == "Save file"
        assert po.unquotefrompo(poelement.msgstr) == ""

    def test_emptyentry(self):
        """checks that an empty properties entry survive into the po file, bug 15"""
        propsource = 'CONFIGENTRY=\n'
        pofile = self.prop2po(propsource)
        poelement = self.singleelement(pofile)
        assert "CONFIGENTRY" in str(poelement)

    def test_tab_at_end_of_string(self):
        """check that we preserve tabs at the end of a string"""
        propsource = r"TAB_AT_END=This setence has a tab at the end.\t"
        pofile = self.prop2po(propsource)
        poelement = self.singleelement(pofile)
        assert po.unquotefrompo(poelement.msgid) == "This setence has a tab at the end.\t"
        propsource = r"SPACE_THEN_TAB_AT_END=This setence has a space then tab at the end. \t"
        pofile = self.prop2po(propsource)
        poelement = self.singleelement(pofile)
        assert po.unquotefrompo(poelement.msgid) == "This setence has a space then tab at the end. \t"
        propsource = r"REAL_TAB_AT_END=This setence has a real tab at the end.	"
        pofile = self.prop2po(propsource)
        poelement = self.singleelement(pofile)
        assert po.unquotefrompo(poelement.msgid) == "This setence has a real tab at the end.	"
        propsource = r"REAL_TAB_THEN_SPACE_AT_END=This setence has a real tab then space at the end.	 "
        pofile = self.prop2po(propsource)
        poelement = self.singleelement(pofile)
        assert po.unquotefrompo(poelement.msgid) == "This setence has a real tab then space at the end.	"
        propsource = r"SPACE_AT_END=This setence will lose its 4 spaces at the end.    "
        pofile = self.prop2po(propsource)
        poelement = self.singleelement(pofile)
        assert po.unquotefrompo(poelement.msgid) == "This setence will lose its 4 spaces at the end."
