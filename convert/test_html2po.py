#!/usr/bin/env python

from translate.convert import html2po
from translate.misc import wStringIO
from translate.storage import po
from translate.storage import html

class TestHTML2PO:
    def html2po(self, markup):
        """Helper to convert html to po without a file."""
        inputfile = wStringIO.StringIO(markup)
        convertor = html2po.html2po()
        outputpo = convertor.convertfile(inputfile, "test", False, False)
        print outputpo
        return outputpo
        
    def test_htmllang(self):
        """Test 'lang' attribute on 'html' element"""
        markup = "<html lang=\"en\"><head><title>My title</title></head><body></body></html>"
        badpo = "<head>"
        pofile = self.html2po(markup)
        assert len(pofile.units) == 1
        assert str(pofile).find(badpo) == -1

    def test_title(self):
        """test that we can extract the <title> tag"""
        markup = "<html><head><title>My title</title></head><body></body></html>"
        expectedpo = "My title"
        pofile = self.html2po(markup)
        assert len(pofile.units) == 1
        assert str(pofile).find(expectedpo) > 0

    def test_tag_p(self):
        """test that we can extract the <p> tag"""
        markup = "<html><head></head><body><p>A paragraph.</p></body></html>"
        expectedpo = "A paragraph."
        pofile = self.html2po(markup)
        assert len(pofile.units) == 1
        assert str(pofile).find(expectedpo) > 0

    def test_tag_a(self):
        """test that we can extract the <a> tag"""
        markup = "<html><head></head><body><p>A paragraph with <a>hyperlink</a>.</p></body></html>"
        expectedpo = "A paragraph with <a>hyperlink</a>."
        pofile = self.html2po(markup)
        assert len(pofile.units) == 1
        assert str(pofile).find(expectedpo) > 0

    def test_tag_img(self):
        """test that we can extract the <a> tag"""
        markup = '''<html><head></head><body><img src="picture.png" alt="A picture"></body></html>'''
        expectedpo = "A picture"
        pofile = self.html2po(markup)
        assert len(pofile.units) == 1
        assert str(pofile).find(expectedpo) > 0

    def test_tag_table_summary(self):
        """test that we can extract summary= """
        markup = '''<html><head></head><body><table summary="Table summary"></table></body></html>'''
        expectedpo = "Table summary"
        pofile = self.html2po(markup)
        assert len(pofile.units) == 1
        assert str(pofile).find(expectedpo) > 0

    def test_table_simple(self):
        """test that we can fully extract a simple table"""
        markup = '''<html><head></head><body><table><tr><th>Heading One</th><th>Heading Two</th><tr><td>One</td><td>Two</td></tr></table></body></html>'''
        pofile = self.html2po(markup)
        assert len(pofile.units) == 4
        assert str(pofile).find("Heading One") > -1
        assert str(pofile).find("Heading Two") > -1
        assert str(pofile).find("One") > -1
        assert str(pofile).find("Two") > -1

    def test_table_complex(self):
        markup = '''<table summary="This is the summary"><caption>A complex table</caption><thead><tr><th>Heading One</th><th>Heading Two</th></thead><tfoot><tr><td>Foot One</td><td>Foot Two</td></tr></tfoot><tbody><tr><td>One</td><td>Two</td></tr></tbody></table>'''
        pofile = self.html2po(markup)
        assert len(pofile.units) == 8
        assert str(pofile).find("This is the summary") > -1
        assert str(pofile).find("A complex table") > -1
        assert str(pofile).find("Heading One") > -1
        assert str(pofile).find("Heading Two") > -1
        assert str(pofile).find("Foot One") > -1
        assert str(pofile).find("Foot Two") > -1
        assert str(pofile).find("One") > -1
        assert str(pofile).find("Two") > -1
        
    def test_nolang(self):
        """Test to see if text is extracted when there is no lang attribute"""
        markup = "<html><head><title>My title</title></head><body><p>My text</p></body></html>"
        badpo = "My text"
        pofile = self.html2po(markup)
        assert len(pofile.units) == 2
        assert str(pofile).find(badpo) == 55
        
    def test_address(self):
        """Test to see if the address element is extracted"""
        markup = "<html lang=\"en\"><head><title>My title</title></head><body><address>My address</address></body></html>"
        goodpo = "My address"
        pofile = self.html2po(markup)
        assert len(pofile.units) == 2
        assert str(pofile).find(goodpo) > -1
        
    def test_headings(self):
        """Test to see if the h* elements are extracted"""
        markup = "<html><head></head><body><h1>Heading One</h1><h2>Heading Two</h2><h3>Heading Three</h3><h4>Heading Four</h4><h5>Heading Five</h5><h6>Heading Six</h6></body></html>"
        pofile = self.html2po(markup)
        assert len(pofile.units) == 6
        assert str(pofile).find("Heading One") > -1
        assert str(pofile).find("Heading Two") > -1
        assert str(pofile).find("Heading Three") > -1
        assert str(pofile).find("Heading Four") > -1
        assert str(pofile).find("Heading Five") > -1
        assert str(pofile).find("Heading Six") > -1
        
    def test_dt(self):
        """Test to see if the definition list title (dt) element is extracted"""
        markup = "<html><head></head><body><dl><dt>Definition List Item Title</dt></dl></body></html>"
        goodpo = "Definition List Item Title"
        pofile = self.html2po(markup)
        assert len(pofile.units) == 1
        assert str(pofile).find(goodpo) > -1
        
    def test_dd(self):
        """Test to see if the definition list description (dd) element is extracted"""
        markup = "<html><head></head><body><dl><dd>Definition List Item Description</dd></dl></body></html>"
        goodpo = "Definition List Item Description"
        pofile = self.html2po(markup)
        assert len(pofile.units) == 1
        assert str(pofile).find(goodpo) > -1

    def test_span(self):
        """test to check that we don't double extract a span item"""
        markup = "<html><head></head><body><p>You are a <span>Spanish</span> sentence.</p></body></html>"
        goodpo = "You are a <span>Spanish</span> sentence."
        pofile = self.html2po(markup)
        assert len(pofile.units) == 1
        assert str(pofile).find(goodpo) > -1

    def test_ul(self):
        """Test to see if the list item <li> is exracted"""
        markup = "<html><head></head><body><ul><li>Unordered One</li><li>Unordered Two</li></ul><ol><li>Ordered One</li><li>Ordered Two</li></ol></body></html>"
        pofile = self.html2po(markup)
        assert len(pofile.units) == 4
        assert str(pofile).find("Unordered One") > -1
        assert str(pofile).find("Unordered Two") > -1
        assert str(pofile).find("Ordered One") > -1
        assert str(pofile).find("Ordered Two") > -1
