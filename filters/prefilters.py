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

# a list of special words with punctuation 
# all apostrophes in the middle of the word are handled already
wordswithpunctuation = ["'n" # afrikaans
                       ]
# map all the words to their non-punctified equivalent
wordswithpunctuation = dict([(word, filter(str.isalnum, word)) for word in wordswithpunctuation])

def filterwordswithpunctuation(str1):
  """goes through a list of known words that have punctuation and removes the punctuation from them"""
  parser = sparse.SimpleParser()
  parser.defaulttokenlist.extend(['\\n', '\\"'])
  words = parser.applytokenizers([str1], [parser.removewhitespace, parser.separatetokens])
  replacements = []
  for n in range(len(words)):
    testword = words[n]
    if len(testword) > 1:
      # remove any ' in the middle of a word...
      removeapostrophe = testword[:1] + testword[1:-1].replace("'","") + testword[-1:]
      if removeapostrophe != testword:
        replacements.append((parser.findtokenpos(str1, words, n), testword, removeapostrophe))
        continue
    npword = wordswithpunctuation.get(testword.lower(), None)
    if npword is not None:
      replacements.append((parser.findtokenpos(str1, words, n), testword, npword))
  newstr1 = ""
  lastpos = 0
  for pos, origword, newword in replacements:
    newstr1 += str1[lastpos:pos]
    newstr1 += newword
    lastpos = pos + len(origword)
  newstr1 += str1[lastpos:]
  return newstr1


