#!/usr/bin/env python
# 
# Copyright 2002, 2003 Zuza Software Foundation
# 
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""this is a set of string filters that should be run before the results are analysed..."""

from translate.misc import sparse
from translate.filters import helpers
from translate.filters import decoration

# filters that the string is passed through before certain tests:

ignoreaccelerators = []

# TODO: have a more intelligent way of selecting sets of accelerators, variables, and tests

oo_accelerators = ("~")
moz_accelerators = ("&")
accelerators = oo_accelerators

accchecks = [decoration.getaccelerators(accelmarker) for accelmarker in accelerators]

acccounters = [decoration.countaccelerators(accelmarker) for accelmarker in accelerators]

oo_varmatches = (("&", ";"), ("%", "%"), ("%", None), ("$(", ")"), ("$", "$"), ("#", "#"))
moz_varmatches = (("&", ";"), ("%", "%"), ("%", 1), ("$", None))
varmatches = oo_varmatches

varchecks = [decoration.getvariables(startmarker, endmarker) for startmarker, endmarker in varmatches]

def filteraccelerators(accelmarker):
  """returns a function that filters accelerators marked using accelmarker in strings"""
  if accelmarker is None: accelmarkerlen = 0
  else: accelmarkerlen = len(accelmarker)
  def filtermarkedaccelerators(str1):
    """modifies the accelerators in str1 marked with a given marker, using a given filter"""
    acclocs = decoration.findaccelerators(str1, accelmarker, ignoreaccelerators)
    fstr1, pos = "", 0
    for accelstart, accelerator in acclocs:
      fstr1 += str1[pos:accelstart]
      fstr1 += accelerator
      pos = accelstart + accelmarkerlen + len(accelerator)
    fstr1 += str1[pos:]
    return fstr1
  return filtermarkedaccelerators

accfilters = [filteraccelerators(accelmarker) for accelmarker in accelerators]

ignorevariables = ["amp"]

def varname(variable, startmarker, endmarker):
  """a simple variable filter that returns the variable name without the marking punctuation"""
  return variable
  # if the punctuation were included, we'd do the following:
  if startmarker is None:
    return variable[:variable.rfind(endmarker)]
  elif endmarker is None:
    return variable[variable.find(startmarker)+len(startmarker):]
  else:
    return variable[variable.find(startmarker)+len(startmarker):variable.rfind(endmarker)]

def filtervariables(startmarker, endmarker, varfilter):
  """returns a function that filters variables marked using startmarker and endmarker in strings"""
  if startmarker is None: startmarkerlen = 0
  else: startmarkerlen = len(startmarker)
  if endmarker is None: endmarkerlen = 0
  elif type(endmarker) == int: endmarkerlen = 0
  else: endmarkerlen = len(endmarker)
  def filtermarkedvariables(str1):
    """modifies the variables in str1 marked with a given marker, using a given filter"""
    varlocs = decoration.findmarkedvariables(str1, startmarker, endmarker)
    fstr1, pos = "", 0
    for varstart, variable in varlocs:
      fstr1 += str1[pos:varstart]
      fstr1 += varfilter(variable, startmarker, endmarker)
      pos = varstart + startmarkerlen + len(variable) + endmarkerlen
    fstr1 += str1[pos:]
    return fstr1
  return filtermarkedvariables

varfilters = [filtervariables(start, end, varname) for start, end in varmatches]

wordswithpunctuation = ["can't", "couldn't", "doesn't", "don't", "wasn't", "won't", "you're",
                        "user's", "system's", "writer's",  # english
                        "'n", "makro's", "scenario's"   # afrikaans
                       ]
# map all the words to their non-punctified equivalent
wordswithpunctuation = dict([(word, filter(str.isalnum, word)) for word in wordswithpunctuation])

def filterwordswithpunctuation(str1):
  """goes through a list of known words that have punctuation and removes the punctuation from them"""
  tokensep = sparse.separategiventokensfn(sparse.defaulttokenlist + ['\\n', '\\"'])
  words = sparse.applytokenizers([str1], [sparse.removewhitespace, tokensep])
  checkwords = dict([(words[n].lower(),n) for n in range(len(words))])
  replacements = []
  for n in range(len(words)):
    testword = words[n]
    npword = wordswithpunctuation.get(testword.lower(), None)
    if npword is not None:
      replacements.append((sparse.findtokenpos(str1, words, n), words[n], npword))
  newstr1 = ""
  lastpos = 0
  for pos, origword, newword in replacements:
    newstr1 += str1[lastpos:pos]
    newstr1 += newword
    lastpos = pos + len(origword)
  newstr1 += str1[lastpos:]
  return newstr1

def accfiltertestmethod(testmethod):
  """returns a function that runs the accelerator filters before the testmethod"""
  return helpers.multifiltertestmethod(testmethod, accfilters)

def varfiltertestmethod(testmethod):
  """returns a function that runs the var filters before the testmethod"""
  return helpers.multifiltertestmethod(testmethod, varfilters)

def puncfiltertestmethod(testmethod):
  """returns a function that runs the punctuation filter before the testmethod"""
  return helpers.filtertestmethod(testmethod, filterwordswithpunctuation)

def accvarpuncfiltertestmethod(testmethod):
  """returns a function that runs the accelerator and var and punctuation filters before the testmethod"""
  return helpers.multifiltertestmethod(testmethod, varfilters + accfilters + [filterwordswithpunctuation])


