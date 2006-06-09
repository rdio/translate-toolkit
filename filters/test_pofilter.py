#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.storage import po
from translate.filters import pofilter
from translate.filters import checks
from translate.misc import wStringIO

class TestPOFilter:
    def poparse(self, posource):
        """helper that parses po source without requiring files"""
        dummyfile = wStringIO.StringIO(posource)
        pofile = po.pofile(dummyfile)
        return pofile

    def pofilter(self, posource, checkerconfig=None, cmdlineoptions=None):
        """helper that parses po source and passes it through a filter"""
        if cmdlineoptions is None:
            cmdlineoptions = []
        options, args = pofilter.cmdlineparser().parse_args(["xxx.po"] + cmdlineoptions)
        checkerclasses = [checks.StandardChecker, pofilter.StandardPOChecker]
        if checkerconfig is None:
          checkerconfig = checks.CheckerConfig()
        checkfilter = pofilter.pocheckfilter(options, checkerclasses, checkerconfig)
        tofile = checkfilter.filterfile(self.poparse(posource))
        return str(tofile)

    def test_simplepass(self):
        """checks that an obviously correct string passes"""
        posource = '#: test.c\nmsgid "test"\nmsgstr "rest"\n'
        poresult = self.pofilter(posource)
        assert poresult == ""

    def test_simplefail(self):
        """checks that an obviously wrong string fails"""
        posource = '#: test.c\nmsgid "test"\nmsgstr "REST"\n'
        poresult = self.pofilter(posource)
        assert poresult != ""

    def test_variables_across_lines(self):
        """Test that variables can span lines and still fail/pass"""
        posource = '#: test.c\nmsgid "At &timeBombURL."\n"label;."\nmsgstr "Tydens &tydBombURL."\n"labeel;."'
        poresult = self.pofilter(posource)
        assert poresult == ""

    def test_ignore_if_already_marked(self):
        """check that we don't add another failing marker is the message is already marked as failed"""
        posource = '# (pofilter) untranslated: checks whether a string has been translated at all\n#: test.c\nmsgid "Simple string"\nmsgstr ""'
        poexpected = posource + '\n'
        poresult = self.pofilter(posource, cmdlineoptions=["--test=untranslated"])
        print poresult
        assert poresult == poexpected

    def test_non_existant_check(self):
	"""check that we report an error if a user tries to run a non-existant test"""
        posource = '#: test.c\nmsgid "test"\nmsgstr "REST"\n'
        poresult = self.pofilter(posource, cmdlineoptions=["-t nonexistant"])
	# TODO Not sure how to check for the stderror result of: warning: could not find filter  nonexistant
        assert poresult == ""

    def test_list_all_tests(self):
	"""lists all available tests"""
        poresult = self.pofilter("", cmdlineoptions=["-l"])
	# TODO again not sure how to check the stderror output
	assert poresult == ""

    def test_test_against_fuzzy(self):
	"""test whether to run tests against fuzzy translations"""
        posource = '#: test.c\n#, fuzzy\nmsgid "test"\nmsgstr "REST"\n'
        poresult = self.pofilter(posource, cmdlineoptions=["--fuzzy"])
	assert poresult != posource
        poresult = self.pofilter(posource, cmdlineoptions=["--nofuzzy"])
	assert poresult == ""
        posource = '#: test.c\nmsgid "test"\nmsgstr "REST"\n'
        poresult = self.pofilter(posource, cmdlineoptions=["--fuzzy"])
	assert poresult != posource
        poresult = self.pofilter(posource, cmdlineoptions=["--nofuzzy"])
	assert poresult != posource

    def test_test_against_review(self):
	"""test whether to run tests against translations marked for review"""
        posource = '#: test.c\n# (review)\nmsgid "test"\nmsgstr "REST"\n'
        poresult = self.pofilter(posource, cmdlineoptions=["--review"])
	assert poresult != posource
        poresult = self.pofilter(posource, cmdlineoptions=["--noreview"])
	assert poresult == ""
        posource = '#: test.c\nmsgid "test"\nmsgstr "REST"\n'
        poresult = self.pofilter(posource, cmdlineoptions=["--review"])
	assert poresult != posource
        poresult = self.pofilter(posource, cmdlineoptions=["--noreview"])
	assert poresult != posource

    def test_isfuzzy(self):
	"""tests the extraction of items marked fuzzy"""
        posource = '#: test.c\n#, fuzzy\nmsgid "test"\nmsgstr "REST"\n'
        poexpected = '# (pofilter) isfuzzy: check if the po element has been marked fuzzy\n#: test.c\n#, fuzzy\nmsgid "test"\nmsgstr "REST"\n'
        poresult = self.pofilter(posource, cmdlineoptions=["--test=isfuzzy"])
	assert poresult == poexpected
        posource = '#: test.c\nmsgid "test"\nmsgstr "REST"\n'
        poresult = self.pofilter(posource, cmdlineoptions=["--test=isfuzzy"])
	assert poresult == ""

    def test_isreview(self):
	"""tests the extraction of items marked review"""
        posource = '# (review)\n#: test.c\nmsgid "test"\nmsgstr "REST"'
        poexpected = posource + '\n'
        poresult = self.pofilter(posource, cmdlineoptions=["--test=isreview"])
	assert poresult == poexpected
        posource = '#: test.c\nmsgid "test"\nmsgstr "REST"\n'
        poresult = self.pofilter(posource, cmdlineoptions=["--test=isreview"])
	assert poresult == ""

    def test_unicode(self):
        """tests that we can handle UTF-8 encoded characters when there is no known header specified encoding"""
        posource = u'#: test.c\nmsgid "Bézier curve"\nmsgstr "Bézier-kurwe"'
        poresult = self.pofilter(posource)
        assert poresult == ''


