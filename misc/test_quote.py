#!/usr/bin/env python

from translate.misc import quote

class TestQuote:

  def test_mozilla_control_escapes(self):
      """test that we do \uNNNN escapes for certain control characters instead of converting to UTF-8 characters"""
      prefix, suffix = "bling", "blang"
      for control in (u"\u0005", u"\u0006", u"\u0007", u"\u0011"):
        string = prefix + control + suffix
        assert quote.escapecontrols(string) == string

  def test_quote_wrapping(self):
      """test that we can wrap strings in double quotes"""
      string = 'A string'
      assert quote.quotestr(string) == '"A string"'
      list = ['One', 'Two']
      assert quote.quotestr(list) == '"One"\n"Two"'

