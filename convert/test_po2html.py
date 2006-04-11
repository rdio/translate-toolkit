#!/usr/bin/env python

from translate.convert import po2html
from translate.convert import test_convert
from translate.misc import wStringIO
from translate.storage import po
from translate.storage import html

class TestPO2Html:
    def converthtml(self, posource, htmltemplate):
        """helper to exercise the command line function"""
        inputfile = wStringIO.StringIO(posource)
        outputfile = wStringIO.StringIO()
        templatefile = wStringIO.StringIO(htmltemplate)
        assert po2html.converthtml(inputfile, outputfile, templatefile)
        print outputfile.getvalue()
        return outputfile.getvalue()

    def test_simple(self):
        """simple po to html test"""
        htmlsource = '<p>A sentence.</p>'
        posource = '''#: html:3\nmsgid "A sentence."\nmsgstr "'n Sin."\n'''
        htmlexpected = '''<p>'n Sin.</p>'''
        assert self.converthtml(posource, htmlsource) == htmlexpected


class TestPO2HtmlCommand(test_convert.TestConvertCommand, TestPO2Html):
    """Tests running actual po2oo commands on files"""
    convertmodule = po2html

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "-tTEMPLATE, --template=TEMPLATE")
        options = self.help_check(options, "-wWRAP, --wrap=WRAP")
        options = self.help_check(options, "--fuzzy")
        options = self.help_check(options, "--nofuzzy", last=True)
