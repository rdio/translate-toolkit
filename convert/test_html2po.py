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
        
    def test_basic(self):
        """Test basic conversion."""
        markup = "<html><head><title>My title</title></head><body><h1>My heading</h1></body></html>"
        pofile = self.html2po(markup)
        assert len(pofile.units) > 0
        
    def test_htmllang(self):
        """Test 'lang' attribute on 'html' element"""
        markup = "<html lang=\"en\"><head><title>My title</title></head><body></body></html>"
        badpo = "<head>"
        pofile = self.html2po(markup)
        print str(pofile)
        assert len(pofile.units) > 0
        assert str(pofile).find(badpo) == -1
