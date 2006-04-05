#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.storage import po
from translate.storage import test_base
from translate.misc.multistring import multistring
from translate.misc import wStringIO

class TestPOUnit(test_base.TestTranslationUnit):
    UnitClass = po.pounit

    def test_plurals(self):
        """Tests that plurals are handled correctly."""
        unit = self.UnitClass("Cow")
        unit.msgid_plural = ['"Cows"']
        assert isinstance(unit.source, multistring)
        assert unit.source.strings == ["Cow", "Cows"]
        assert unit.source == "Cow"

        unit.target = ["Koei", "Koeie"]
        assert isinstance(unit.target, multistring)
        assert unit.target.strings == ["Koei", "Koeie"]
        assert unit.target == "Koei"

        unit.target = {0:"Koei", 3:"Koeie"}
        assert isinstance(unit.target, multistring)
        assert unit.target.strings == ["Koei", "Koeie"]
        assert unit.target == "Koei"

        unit.target = [u"Sk\u00ear", u"Sk\u00eare"]
        assert isinstance(unit.target, multistring)
        assert unit.target.strings == [u"Sk\u00ear", u"Sk\u00eare"]
        assert unit.target.strings == [u"Sk\u00ear", u"Sk\u00eare"]
        assert unit.target == u"Sk\u00ear"

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

    def pomerge(self, oldmessage, newmessage):
        """helper that merges two messages"""
        dummyfile = wStringIO.StringIO(oldmessage)
        oldpofile = po.pofile(dummyfile)
        oldunit = oldpofile.units[0]
        dummyfile2 = wStringIO.StringIO(newmessage)
        if newmessage:
          newpofile = po.pofile(dummyfile2)
          newunit = newpofile.units[0]
        else:
          newunit = po.pounit()
        oldunit.merge(newunit)
        print oldunit
        return str(oldunit)

    def test_simpleentry(self):
        """checks that a simple po entry is parsed correctly"""
        posource = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        pofile = self.poparse(posource)
        assert len(pofile.units) == 1
        thepo = pofile.units[0]
        assert thepo.getids() == ["test.c"]
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
        assert pofile.units[0].getids() == ["source1", "source2"]

    def test_merge_mixed_sources(self):
        """checks that merging works with different source location styles"""
        posource = '''
#: source1
#: source2
msgid "test"
msgstr ""

#: source1 source2
msgid "test"
msgstr ""
'''
        pofile = self.poparse(posource)
        print str(pofile)
        assert len(pofile.units) == 2
        pofile.removeduplicates("merge")
        print str(pofile)
        assert len(pofile.units) == 1
        assert pofile.units[0].getids() == ["source1", "source2"]

    def test_merge_blanks(self):
        """checks that merging adds msgid_comments to blanks"""
        posource = '#: source1\nmsgid ""\nmsgstr ""\n\n#: source2\nmsgid ""\nmsgstr ""\n'
        pofile = self.poparse(posource)
        assert len(pofile.units) == 2
        pofile.removeduplicates("merge")
        assert len(pofile.units) == 2
        assert po.unquotefrompo(pofile.units[0].msgidcomments) == "_: source1\\n"
        assert po.unquotefrompo(pofile.units[1].msgidcomments) == "_: source2\\n"

    def test_keep_blanks(self):
        """checks that keeping keeps blanks and doesn't add msgid_comments"""
        posource = '#: source1\nmsgid ""\nmsgstr ""\n\n#: source2\nmsgid ""\nmsgstr ""\n'
        pofile = self.poparse(posource)
        assert len(pofile.units) == 2
        pofile.removeduplicates("keep")
        assert len(pofile.units) == 2
        # check we don't add msgidcomments
        assert po.unquotefrompo(pofile.units[0].msgidcomments) == ""
        assert po.unquotefrompo(pofile.units[1].msgidcomments) == ""

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

    def test_output_str_unicode(self):
        """checks that we can str(element) which is in unicode"""
        posource = u'''#: nb\nmsgid "Norwegian Bokm\xe5l"\nmsgstr ""\n'''
        pofile = po.pofile(wStringIO.StringIO(posource.encode("UTF-8")), encoding="UTF-8")
        assert len(pofile.units) == 1
        print str(pofile)
        thepo = pofile.units[0]
        assert str(thepo) == posource.encode("UTF-8")
        # extra test: what if we set the msgid to a unicode? this happens in prop2po etc
        thepo.source = u"Norwegian Bokm\xe5l"
        assert str(thepo) == posource.encode("UTF-8")
        # Now if we set the msgstr to Unicode
        # this is an escaped half character (1/2)
        halfstr = "\xbd ...".decode("latin-1")
        thepo.target = halfstr
        assert halfstr in str(thepo).decode("UTF-8")
        thepo.target = halfstr.encode("UTF-8")
        assert halfstr.encode("UTF-8") in thepo.getoutput()

    def test_plurals(self):
        posource = r'''msgid "Cow"
msgid_plural "Cows"
msgstr[0] "Koei"
msgstr[1] "Koeie"
'''
        pofile = po.pofile(wStringIO.StringIO(posource))
        assert len(pofile.units) == 1
        unit = pofile.units[0]
        assert isinstance(unit.target, multistring)
        print unit.target.strings
        assert unit.target == "Koei"
        assert unit.target.strings == ["Koei", "Koeie"]

        posource = r'''msgid "Skaap"
msgid_plural "Skape"
msgstr[0] "Sheep"
'''
        pofile = po.pofile(wStringIO.StringIO(posource))
        assert len(pofile.units) == 1
        unit = pofile.units[0]
        assert isinstance(unit.target, multistring)
        print unit.target.strings
        assert unit.target == "Sheep"
        assert unit.target.strings == ["Sheep"]

    def test_posections(self):
        """checks the content of all the expected sections of a PO message"""
        posource = '# other comment\n#. automatic comment\n#: source comment\n#, fuzzy\nmsgid "One"\nmsgstr "Een"\n'
        pofile = self.poparse(posource)
        print pofile
        assert len(pofile.units) == 1
        assert str(pofile) == posource + '\n'
        assert pofile.units[0].othercomments == ["# other comment\n"]
        assert pofile.units[0].automaticcomments == ["#. automatic comment\n"]
        assert pofile.units[0].sourcecomments == ["#: source comment\n"]
        assert pofile.units[0].typecomments == ["#, fuzzy\n"]

    def test_obsolete(self):
        """Tests that obsolete messages work"""
        posource = '#~ msgid "Old thing"\n#~ msgstr "Ou ding"\n"'
        pofile = self.poparse(posource)
        assert pofile.isempty()
        assert len(pofile.units) == 1
        unit = pofile.units[0]
        assert unit.isobsolete()
        assert unit.obsoletemessages == ['#~ msgid "Old thing"\n', '#~ msgstr "Ou ding"\n']

    def test_makeobsolete(self):
        """Tests making a unit obsolete"""
        posource = '#. The automatic one\n#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        poexpected = '#~ msgid "test"\n#~ msgstr "rest"\n'
        pofile = self.poparse(posource)
        print pofile
        unit = pofile.units[0]
        assert not unit.isobsolete()
        unit.makeobsolete()
        assert unit.isobsolete()
        print pofile
        assert str(unit) == poexpected
        
        posource = r'''msgid "Cow"
msgid_plural "Cows"
msgstr[0] "Koei"
msgstr[1] "Koeie"
'''
        poexpected = '''#~ msgid "Cow"
#~ msgid_plural "Cows"
#~ msgstr[0] "Koei"
#~ msgstr[1] "Koeie"
'''
        pofile = self.poparse(posource)
        print pofile
        unit = pofile.units[0]
        assert not unit.isobsolete()
        unit.makeobsolete()
        assert unit.isobsolete()
        print pofile
        assert str(unit) == poexpected

    def test_merging_automaticcomments(self):
        """checks that new automatic comments override old ones"""
        oldsource = '#. old comment\n#: line:10\nmsgid "One"\nmsgstr "Een"\n'
        newsource = '#. new comment\n#: line:10\nmsgid "One"\nmsgstr ""\n'
        expected = '#. new comment\n#: line:10\nmsgid "One"\nmsgstr "Een"\n'
        assert self.pomerge(newsource, oldsource) == expected

    def test_unassociated_comments(self):
	"""tests behaviour of unassociated comments."""
	oldsource = '# old lonesome comment\n\nmsgid "one"\nmsgstr "een"\n'
        oldfile = self.poparse(oldsource)
	print "__str__", str(oldfile)
	assert len(oldfile.units) == 2
	assert str(oldfile).find("# old lonesome comment\n\n") >= 0
