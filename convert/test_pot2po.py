#!/usr/bin/env python

from translate.convert import pot2po
from translate.misc import wStringIO
from translate.storage import po
from py import test
import warnings

class TestPO2DTD:
    def setup_method(self, method):
        warnings.resetwarnings()

    def teardown_method(self, method):
        warnings.resetwarnings()

    def convertpot(self, potsource, posource=None):
        """helper that converts pot source to po source without requiring files"""
        potfile = wStringIO.StringIO(potsource)
        if posource:
          pofile = wStringIO.StringIO(posource)
        else:
          pofile = None
        pooutfile = wStringIO.StringIO()
        pot2po.convertpot(potfile, pooutfile, pofile)
        pooutfile.seek(0)
	return po.pofile(pooutfile.read())

    def singleunit(self, pofile):
        """checks that the pofile contains a single non-header unit, and returns it"""
        assert len(pofile.units) == 2
        assert pofile.units[0].isheader()
        return pofile.units[1]

    def test_convertpot_blank(self):
        """checks that the convertpot function is working for a simple file initialisation"""
        potsource = '''#: simple.label\n#: simple.accesskey\nmsgid "A &hard coded newline.\\n"\nmsgstr ""\n'''
        newpo = self.convertpot(potsource)
        assert str(self.singleunit(newpo)) == potsource

    def test_merging_simple(self):
        """checks that the convertpot function is working for a simple merge"""
        potsource = '''#: simple.label\n#: simple.accesskey\nmsgid "A &hard coded newline.\\n"\nmsgstr ""\n'''
        posource = '''#: simple.label\n#: simple.accesskey\nmsgid "A &hard coded newline.\\n"\nmsgstr "&Hart gekoeerde nuwe lyne\\n"\n'''
        newpo = self.convertpot(potsource, posource)
        assert str(self.singleunit(newpo)) == posource

    def test_merging_messages_marked_fuzzy(self):
        """test that when we merge PO files with a fuzzy message that it remains fuzzy"""
        potsource = '''#: simple.label\n#: simple.accesskey\nmsgid "A &hard coded newline.\\n"\nmsgstr ""\n'''
        posource = '''#: simple.label\n#: simple.accesskey\n#, fuzzy\nmsgid "A &hard coded newline.\\n"\nmsgstr "&Hart gekoeerde nuwe lyne\\n"\n'''
        newpo = self.convertpot(potsource, posource)
        assert str(self.singleunit(newpo)) == posource

    def xtest_merging_msgid_change(self):
        """tests that if the msgid changes but the location stays the same that we merge"""
        potsource = '''#: simple.label\n#: simple.accesskey\nmsgid "Its &hard coding a newline.\\n"\nmsgstr ""\n'''
        posource = '''#: simple.label\n#: simple.accesskey\nmsgid "A &hard coded newline.\\n"\nmsgstr "&Hart gekoeerde nuwe lyne\\n"\n'''
        poexpected = '''#: simple.label\n#: simple.accesskey\n#, fuzzy\nmsgid "Its &hard coding a newline.\\n"\nmsgstr "&Hart gekoeerde nuwe lyne\\n"\n'''
        newpo = self.convertpot(potsource, posource)
        print newpo
        assert str(self.singleunit(newpo)) == poexpected

    def xtest_merging_location_change(self):
        """tests that if the msgid changes but the location stays the same that we merge"""
        potsource = '''#: new_simple.label\n#: new_simple.accesskey\nmsgid "A &hard coded newline.\\n"\nmsgstr ""\n'''
        posource = '''#: simple.label\n#: simple.accesskey\nmsgid "A &hard coded newline.\\n"\nmsgstr "&Hart gekoeerde nuwe lyne\\n"\n'''
        poexpected = '''#: new_simple.label\n#: new_simple.accesskey\n#, fuzzy\nmsgid "A &hard coded newline.\\n"\nmsgstr "&Hart gekoeerde nuwe lyne\\n"\n'''
        newpo = self.convertpot(potsource, posource)
        print newpo
        assert str(self.singleunit(newpo)) == poexpected

    def test_lines_cut_differently(self):
        """checks that the convertpot function is working"""
        potsource = '''#: simple.label\nmsgid "Line split "\n"differently"\nmsgstr ""\n'''
        posource = '''#: simple.label\nmsgid "Line"\n" split differently"\nmsgstr "Lyne verskillend gesny"\n'''
        poexpected = '''#: simple.label\nmsgid "Line split "\n"differently"\nmsgstr "Lyne verskillend gesny"\n'''
        newpo = self.convertpot(potsource, posource)
        newpounit = self.singleunit(newpo)
        print newpounit
        assert str(newpounit) == poexpected

    def test_merging_automatic_comments(self):
        """ensure that we can merge #. comments correctly"""
        potsource = '''#. Row 35\nmsgid "&About"\nmsgstr ""\n'''
        posource = '''#. Row 35\nmsgid "&About"\nmsgstr "&Info"\n'''
        newpo = self.convertpot(potsource, posource)
        newpounit = self.singleunit(newpo)
        print newpounit
        assert str(newpounit) == posource
        
