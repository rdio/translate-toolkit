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
        return outputpo
        
    def test_htmllang(self):
        """Test 'lang' attribute on 'html' element"""
        markup = "<html lang=\"en\"><head><title>My title</title></head><body></body></html>"
        badpo = "<head>"
        pofile = self.html2po(markup)
        print str(pofile)
        assert len(pofile.units) == 1
        assert str(pofile).find(badpo) == -1
        
    def test_nolang(self):
        """Test to see if text is extracted when there is no lang attribute"""
        markup = "<html><head><title>My title</title></head><body><p>My text</p></body></html>"
        badpo = "My text"
        pofile = self.html2po(markup)
        print str(pofile)
        assert len(pofile.units) == 2
        assert str(pofile).find(badpo) == -1
        
    def test_address(self):
        """Test to see if the address element is extracted"""
        markup = "<html lang=\"en\"><head><title>My title</title></head><body><address>My address</address></body></html>"
        goodpo = "My address"
        pofile = self.html2po(markup)
        print str(pofile)
        assert len(pofile.units) == 2
        assert str(pofile).find(goodpo) > -1
        
    def test_headings(self):
        """Test to see if the h4, h5 and h6 elements are extracted"""
        markup = "<html lang=\"en\"><head><title>My title</title></head><body><h4>Heading Four</h4><h5>Heading Five</h5><h6>Heading Six</h6></body></html>"
        pofile = self.html2po(markup)
        print str(pofile)
        assert len(pofile.units) == 4
        assert str(pofile).find("Heading Four") > -1
        assert str(pofile).find("Heading Five") > -1
        assert str(pofile).find("Heading Six") > -1
        
    def test_dt(self):
        """Test to see if the definition list title (dt) element is extracted"""
        markup = "<html lang=\"en\"><head><title>My title</title></head><body><dl><dt>Definition List Item Title</dt></dl></body></html>"
        goodpo = "Definition List Item Title"
        pofile = self.html2po(markup)
        print str(pofile)
        assert len(pofile.units) == 2
        assert str(pofile).find(goodpo) > -1
        
    def test_dd(self):
        """Test to see if the definition list description (dd) element is extracted"""
        markup = "<html lang=\"en\"><head><title>My title</title></head><body><dl><dd>Definition List Item Description</dd></dl></body></html>"
        goodpo = "Definition List Item Description"
        pofile = self.html2po(markup)
        print str(pofile)
        assert len(pofile.units) == 2
        assert str(pofile).find(goodpo) > -1
