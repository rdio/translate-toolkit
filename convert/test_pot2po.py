#!/usr/bin/env python

from translate.convert import pot2po
from translate.convert import test_convert
from translate.misc import wStringIO
from translate.storage import po
from py import test
import warnings

class TestPOT2PO:
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
        print pofile.units[1]
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
        """tests that if the location changes but the msgid stays the same that we merge"""
        potsource = '''#: new_simple.label\n#: new_simple.accesskey\nmsgid "A &hard coded newline.\\n"\nmsgstr ""\n'''
        posource = '''#: simple.label\n#: simple.accesskey\nmsgid "A &hard coded newline.\\n"\nmsgstr "&Hart gekoeerde nuwe lyne\\n"\n'''
        poexpected = '''#: new_simple.label\n#: new_simple.accesskey\n#, fuzzy\nmsgid "A &hard coded newline.\\n"\nmsgstr "&Hart gekoeerde nuwe lyne\\n"\n'''
        newpo = self.convertpot(potsource, posource)
        print newpo
        assert str(self.singleunit(newpo)) == poexpected

    def test_merging_location_and_whitespace_change(self):
        """test that even if the location changes that if the msgid only has whitespace changes we can still merge"""
        potsource = '''#: singlespace.label\n#: singlespace.accesskey\nmsgid "&We have spaces"\nmsgstr ""\n'''
        posource = '''#: doublespace.label\n#: doublespace.accesskey\nmsgid "&We  have  spaces"\nmsgstr "&One  het  spasies"\n'''
        poexpected = '''#: singlespace.label\n#: singlespace.accesskey\n#, fuzzy\nmsgid "&We have spaces"\nmsgstr "&One  het  spasies"\n'''
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
        assert str(newpounit) == poexpected

    def test_merging_automatic_comments_dont_duplicate(self):
        """ensure that we can merge #. comments correctly"""
        potsource = '''#. Row 35\nmsgid "&About"\nmsgstr ""\n'''
        posource = '''#. Row 35\nmsgid "&About"\nmsgstr "&Info"\n'''
        newpo = self.convertpot(potsource, posource)
        newpounit = self.singleunit(newpo)
        assert str(newpounit) == posource

    def test_merging_automatic_comments_new_overides_old(self):
        """ensure that new #. comments override the old comments"""
        potsource = '''#. new comment\n#: someline.c\nmsgid "&About"\nmsgstr ""\n'''
        posource = '''#. old comment\n#: someline.c\nmsgid "&About"\nmsgstr "&Info"\n'''
        poexpected = '''#. new comment\n#: someline.c\nmsgid "&About"\nmsgstr "&Info"\n'''
        newpo = self.convertpot(potsource, posource)
        newpounit = self.singleunit(newpo)
        assert str(newpounit) == poexpected
        
    def test_merging_obsoleting_messages(self):
        """check that we obsolete messages no longer present in the new file"""
        potsource = ''
        posource = '#: obsoleteme:10\nmsgid "One"\nmsgstr "Een"\n'
        expected = '#~ msgid "One"\n#~ msgstr "Een"\n'
        newpo = self.convertpot(potsource, posource)
        print str(newpo)
        newpounit = self.singleunit(newpo)
        assert str(newpounit) == expected

    def test_merging_new_before_obsolete(self):
        """test to check that we place new blank message before obsolete messages"""
        potsource = '''#: newline.c\nmsgid "&About"\nmsgstr ""\n'''
        posource = '''#~ msgid "Old"\n#~ msgstr "Oud"\n'''
        newpo = self.convertpot(potsource, posource)
        assert len(newpo.units) == 3
        assert newpo.units[0].isheader()
        assert newpo.units[2].isobsolete()
        newpo.units = newpo.units[1:]
        assert str(newpo) == potsource + "\n" + posource

    def test_merging_resurect_obsolete_messages(self):
        """check that we can reuse old obsolete messages if the message comes back"""
        potsource = '''#: resurect.c\nmsgid "&About"\nmsgstr ""\n'''
        posource = '''#~ msgid "&About"\n#~ msgstr "&Omtrent"\n'''
        expected = '''#: resurect.c\nmsgid "&About"\nmsgstr "&Omtrent"\n'''
        newpo = self.convertpot(potsource, posource)
        print newpo
        assert len(newpo.units) == 2
        assert newpo.units[0].isheader()
        newpounit = self.singleunit(newpo)
        assert str(newpounit) == expected

    def test_header_initialisation(self):
        """test to check that we initialise the header correctly"""
        sourcepot = po.pofile()
        sourcepot.units.append(sourcepot.makeheader())
        print sourcepot
        assert sourcepot.units[0].isheader()
        newpo = self.convertpot(sourcepot.__str__())
        print newpo
        assert newpo.units[0].isheader()
        sourcepotrevison = sourcepot.parseheader().get('PO-Revision-Date', None)
        newporevison = newpo.parseheader().get('PO-Revision-Date', None)
        assert sourcepotrevison == newporevison

class TestPOT2POCommand(test_convert.TestConvertCommand, TestPOT2PO):
    """Tests running actual pot2po commands on files"""
    convertmodule = pot2po

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "-tTEMPLATE, --template=TEMPLATE")
        options = self.help_check(options, "-P, --pot", last=True)

