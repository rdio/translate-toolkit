#!/usr/bin/env python

from translate.convert import html2po
from translate.convert import test_convert
from translate.misc import wStringIO
from translate.storage import po
from translate.storage import html

class TestHTML2PO:
    def html2po(self, markup):
        """Helper to convert html to po without a file."""
        inputfile = wStringIO.StringIO(markup)
        convertor = html2po.html2po()
        outputpo = convertor.convertfile(inputfile, "test", False, False)
        return outputpo

    def countunits(self, pofile, expected):
        """helper to check that we got the expected number of messages"""
        actual = len(pofile.units)
        if pofile.units[0].isheader():
          actual = actual - 1
        print pofile
        assert actual == expected

    def compareunit(self, pofile, unitnumber, expected):
        """helper to validate a PO message"""
        if not pofile.units[0].isheader():
          unitnumber = unitnumber - 1
        print pofile.units[unitnumber]
        print expected
        assert str(pofile.units[unitnumber].source) == expected

    def check_single(self, markup, itemtext):
        """checks that converting this markup produces a single element with value itemtext"""
        pofile = self.html2po(markup)
        self.countunits(pofile, 1)
        self.compareunit(pofile, 1, itemtext)

    def check_null(self, markup):
        """checks that converting this markup produces no elements"""
        pofile = self.html2po(markup)
        self.countunits(pofile, 0)

    def test_htmllang(self):
        """test to ensure that we no longer use the lang attribure"""
        markup = '''<html lang="en"><head><title>My title</title></head><body></body></html>'''
        pofile = self.html2po(markup)
        self.countunits(pofile, 1)
        # Check that the first item is the <title> not <head>
        self.compareunit(pofile, 1, "My title")

    def test_title(self):
        """test that we can extract the <title> tag"""
        self.check_single("<html><head><title>My title</title></head><body></body></html>", "My title")

    def test_meta(self):
        """test that we can extract certian <meta> info from <head>"""
        self.check_single('''<html><head><meta name="keywords" content="these are keywords"></head><body></body></html>''', "these are keywords")

    def test_tag_p(self):
        """test that we can extract the <p> tag"""
        self.check_single("<html><head></head><body><p>A paragraph.</p></body></html>", "A paragraph.")
        markup = "<p>First line.<br>Second line.</p>"
        pofile = self.html2po(markup)
        self.compareunit(pofile, 1, "First line.<br>Second line.")

    def test_tag_a(self):
        """test that we can extract the <a> tag"""
        self.check_single("<html><head></head><body><p>A paragraph with <a>hyperlink</a>.</p></body></html>", "A paragraph with <a>hyperlink</a>.")

    def test_tag_img(self):
        """test that we can extract the <a> tag"""
        self.check_single('''<html><head></head><body><img src="picture.png" alt="A picture"></body></html>''', "A picture")

    def test_tag_table_summary(self):
        """test that we can extract summary= """
        self.check_single( '''<html><head></head><body><table summary="Table summary"></table></body></html>''', "Table summary")

    def test_table_simple(self):
        """test that we can fully extract a simple table"""
        markup = '''<html><head></head><body><table><tr><th>Heading One</th><th>Heading Two</th><tr><td>One</td><td>Two</td></tr></table></body></html>'''
        pofile = self.html2po(markup)
        self.countunits(pofile, 4)
        self.compareunit(pofile, 1, "Heading One")
        self.compareunit(pofile, 2, "Heading Two")
        self.compareunit(pofile, 3, "One")
        self.compareunit(pofile, 4, "Two")

    def test_table_complex(self):
        markup = '''<table summary="This is the summary"><caption>A caption</caption><thead><tr><th abbr="Head 1">Heading One</th><th>Heading Two</th></thead><tfoot><tr><td>Foot One</td><td>Foot Two</td></tr></tfoot><tbody><tr><td>One</td><td>Two</td></tr></tbody></table>'''
        pofile = self.html2po(markup)
        self.countunits(pofile, 9)
        self.compareunit(pofile, 1, "This is the summary")
        self.compareunit(pofile, 2, "A caption")
        self.compareunit(pofile, 3, "Head 1")
        self.compareunit(pofile, 4, "Heading One")
        self.compareunit(pofile, 5, "Heading Two")
        self.compareunit(pofile, 6, "Foot One")
        self.compareunit(pofile, 7, "Foot Two")
        self.compareunit(pofile, 8, "One")
        self.compareunit(pofile, 9, "Two")

    def test_table_empty(self):
        """test that we ignore tables that are empty ie they have no translatanle content"""
        self.check_null('''<html><head></head><body><table><tr><td><img src="bob.png"></td></tr></table></body></html>''')
        self.check_null('''<html><head></head><body><table><tr><td>&nbsp;</td></tr></table></body></html>''')
        self.check_null('''<html><head></head><body><table><tr><td><strong></strong></td></tr></table></body></html>''')
        
    def test_address(self):
        """Test to see if the address element is extracted"""
        self.check_single("<body><address>My address</address></body>", "My address")
        
    def test_headings(self):
        """Test to see if the h* elements are extracted"""
        markup = "<html><head></head><body><h1>Heading One</h1><h2>Heading Two</h2><h3>Heading Three</h3><h4>Heading Four</h4><h5>Heading Five</h5><h6>Heading Six</h6></body></html>"
        pofile = self.html2po(markup)
        self.countunits(pofile, 6)
        self.compareunit(pofile, 1, "Heading One")
        self.compareunit(pofile, 2, "Heading Two")
        self.compareunit(pofile, 3, "Heading Three")
        self.compareunit(pofile, 4, "Heading Four")
        self.compareunit(pofile, 5, "Heading Five")
        self.compareunit(pofile, 6, "Heading Six")
        
    def test_dt(self):
        """Test to see if the definition list title (dt) element is extracted"""
        self.check_single("<html><head></head><body><dl><dt>Definition List Item Title</dt></dl></body></html>", "Definition List Item Title")
        
    def test_dd(self):
        """Test to see if the definition list description (dd) element is extracted"""
        self.check_single("<html><head></head><body><dl><dd>Definition List Item Description</dd></dl></body></html>", "Definition List Item Description")

    def test_span(self):
        """test to check that we don't double extract a span item"""
        self.check_single("<html><head></head><body><p>You are a <span>Spanish</span> sentence.</p></body></html>", "You are a <span>Spanish</span> sentence.")

    def test_ul(self):
        """Test to see if the list item <li> is exracted"""
        markup = "<html><head></head><body><ul><li>Unordered One</li><li>Unordered Two</li></ul><ol><li>Ordered One</li><li>Ordered Two</li></ol></body></html>"
        pofile = self.html2po(markup)
        self.countunits(pofile, 4)
        self.compareunit(pofile, 1, "Unordered One")
        self.compareunit(pofile, 2, "Unordered Two")
        self.compareunit(pofile, 3, "Ordered One")
        self.compareunit(pofile, 4, "Ordered Two")

    def test_duplicates(self):
        """check that we use the default style of msgid_comments to disambiguate duplicate messages"""
        markup = "<html><head></head><body><p>Duplicate</p><p>Duplicate</p></body></html>"
        pofile = self.html2po(markup)
        self.countunits(pofile, 2)
        # FIXME change this so that we check that the KDE comment is correctly added
        self.compareunit(pofile, 1, "Duplicate")
        self.compareunit(pofile, 2, "Duplicate")

    def test_multiline(self):
        """check that we correctly place double quotes around strings from multiline tag content"""
        markup = '<p>First line.\nSecond line.\nThird line.</p>'
        expected = 'msgid ""\n"First line."\n"Second line."\n"Third line."\n'
        pofile = self.html2po(markup)
        self.countunits(pofile, 1)
        print expected
        assert pofile.units[0].getmsgpartstr("msgid", pofile.units[0].msgid) == expected

    def test_multiline_reflow(self):
        """check that we reflow multiline content to make it more readable for translators"""
        self.check_single('''<td valign="middle" width="96%"><font class="headingwhite">South
                  Africa</font></td>''', '''<font class="headingwhite">South Africa</font>''')

class TestHTML2POCommand(test_convert.TestConvertCommand, TestHTML2PO):
    """Tests running actual html2po commands on files"""
    convertmodule = html2po
    defaultoptions = {"progress": "none"}

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "-P, --pot")
        options = self.help_check(options, "--duplicates=DUPLICATESTYLE")
        options = self.help_check(options, "-u, --untagged", last=True)
