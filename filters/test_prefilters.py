#!/usr/bin/env python

"""tests decoration handling functions that are used by checks"""

from translate.filters import prefilters

def test_filterwordswithpunctuation():
    string = "Nothing in here."
    filtered = prefilters.filterwordswithpunctuation(string)
    assert filtered == string
    string = "'n Boom het 'n tak."
    filtered = prefilters.filterwordswithpunctuation(string)
    assert filtered == "n Boom het n tak."
