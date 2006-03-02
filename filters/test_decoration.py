#!/usr/bin/env python

"""tests decoration handling functions that are used by checks"""

from translate.filters import decoration

def test_find_marked_variables():
    vars = decoration.findmarkedvariables("The <variable> string", "<", ">")
    assert vars == [(4, "variable")]
    vars = decoration.findmarkedvariables("The $variable string", "$", 1)
    assert vars == [(4, "v")]
    vars = decoration.findmarkedvariables("The $variable string", "$", None)
    assert vars == [(4, "variable")]
    vars = decoration.findmarkedvariables("The $variable string", "$", 0)
    assert vars == [(4, "")]

