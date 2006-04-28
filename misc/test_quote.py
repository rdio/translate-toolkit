#!/usr/bin/env python

from translate.misc import quote

def test_find_all():
    """tests the find_all function"""
    assert quote.find_all("", "a") == []
    assert quote.find_all("a", "b") == []
    assert quote.find_all("a", "a") == [0]
    assert quote.find_all("aa", "a") == [0, 1]
    assert quote.find_all("abba", "ba") == [2]
    # check we skip the whole instance
    assert quote.find_all("banana", "ana") == [1]

def test_extract():
    """tests the extract function"""
    assert quote.extract("the <quoted> part", "<", ">", "\\", 0) == ("<quoted>", False)
    assert quote.extract("the 'quoted' part", "'", "'", "\\", 0) == ("'quoted'", False)
    assert quote.extract("the 'isn\\'t escaping fun' part", "'", "'", "\\", 0) == ("'isn\\'t escaping fun'", False)
    assert quote.extract("the 'isn\\'t something ", "'", "'", "\\", 0) == ("'isn\\'t something ", True)
    assert quote.extract("<quoted>\\", "<", ">", "\\", 0) == ("<quoted>", False)
    assert quote.extract("<quoted>\\\\<again>", "<", ">", "\\", 0) == ("<quoted><again>", False)
    assert quote.extract("<quoted\\>", "<", ">", "\\", 0) == ("<quoted\\>", True)

def test_extractwithoutquotes():
    """tests the extract function"""
    assert quote.extractwithoutquotes("the <quoted> part", "<", ">", "\\", 0) == ("quoted", False)
    assert quote.extractwithoutquotes("the 'quoted' part", "'", "'", "\\", 0) == ("quoted", False)
    assert quote.extractwithoutquotes("the 'isn\\'t escaping fun' part", "'", "'", "\\", 0) == ("isn\\'t escaping fun", False)
    assert quote.extractwithoutquotes("the 'isn\\'t something ", "'", "'", "\\", 0) == ("isn\\'t something ", True)
    assert quote.extractwithoutquotes("<quoted>\\", "<", ">", "\\", 0) == ("quoted", False)
    assert quote.extractwithoutquotes("<quoted>\\\\<again>", "<", ">", "\\", 0) == ("quotedagain", False)
    # don't include escapes...
    assert quote.extractwithoutquotes("the 'isn\\'t escaping fun' part", "'", "'", "\\", 0, False) == ("isn't escaping fun", False)
    assert quote.extractwithoutquotes("the 'isn\\'t something ", "'", "'", "\\", 0, False) == ("isn't something ", True)
    assert quote.extractwithoutquotes("<quoted\\", "<", ">", "\\", 0, False) == ("quoted\\", True)
    assert quote.extractwithoutquotes("<quoted><again\\\\", "<", ">", "\\", 0, False) == ("quotedagain\\", True)
    # escaping of quote char
    # TODO: this currently fails with ('quoted', False)
    assert quote.extractwithoutquotes("<quoted\\>", "<", ">", "\\", 0, False) == ("quoted>", True)

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

