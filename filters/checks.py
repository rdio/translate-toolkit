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

"""this is a set of validation checks that can be done on original strings and translations"""

from translate.misc import sparse
from translate.filters import helpers
from translate.filters import decoration
from translate.filters import prefilters

# actual test methods

def untranslated(str1, str2):
  """checks whether a string has been translated at all"""
  return not (len(str1.strip()) > 0 and len(str2) == 0)

def translationdifferent(str1, str2):
  """checks whether a translation is basically identical to the original string"""
  return str1.strip().lower() != str2.strip().lower()

def blanktranslation(str1, str2):
  """checks whether a translation is totally blank"""
  return not (len(str1.strip()) > 0 and len(str2) != 0 and len(str2.strip()) == 0)

def shorttranslation(str1, str2):
  """checks whether a translation is much shorter than the original string"""
  return not (len(str1.strip()) > 0 and 0 < len(str2.strip()) < len(str1.strip()) * 0.1)

def escapeconsistent(str1, str2):
  """checks whether escaping is consistent between the two strings"""
  return helpers.countsmatch(str1, str2, ("\\", "\\\\"))

def quoteconsistent(str1, str2):
  """checks whether quoting is consistent between the two strings"""
  return helpers.countsmatch(str1, str2, ('"', "'", '""', "''", '\\"', "\\'"))
quoteconsistent = prefilters.accvarpuncfiltertestmethod(quoteconsistent)

def acceleratorsconsistent(str1, str2):
  """checks whether accelerators are consistent between the two strings"""
  return helpers.funcsmatch(str1, str2, acccounters)
acceleratorsconsistent = prefilters.varfiltertestmethod(acceleratorsconsistent)

def variablesconsistent(str1, str2):
  """checks whether variables of various forms are consistent between the two strings"""
  return helpers.funcsmatch(str1, str2, prefilters.varchecks)

def startandend(str1, str2):
  """checks whether punctuation at the beginning and end of the strings match"""
  return helpers.funcsmatch(str1, str2, (decoration.puncstart, decoration.puncend))
startandend = prefilters.accvarpuncfiltertestmethod(startandend)

def purepunctuationunchanged(str1, str2):
  """checks that strings that are purely punctuation are not changed"""
  # this test is a subset of startandend
  if (decoration.ispurepunctuation(str1)):
    return str1 == str2
  return 1

def simplecapitalisation(str1, str2):
  """checks the capitalisation of two strings isn't wildly different"""
  capitals1, capitals2 = helpers.filtercount(str1, str.isupper), helpers.filtercount(str2, str.isupper)
  # some heuristic tests to try and see that the style of capitals is vaguely the same
  if capitals1 == 0 or capitals1 == 1:
    return capitals2 == capitals1
  elif capitals1 < len(str1) / 10:
    return capitals2 < len(str2) / 10
  elif len(str1) < 10:
    return abs(capitals1 - capitals2) < 3
  elif capitals1 > len(str1) * 6 / 10:
    return capitals2 > len(str2) * 6 / 10
  else:
    return abs(capitals1 - capitals2) < (len(str1) + len(str2)) / 6 

alltests = (untranslated, escapeconsistent, quoteconsistent, acceleratorsconsistent, variablesconsistent,
            startandend, purepunctuationunchanged, simplecapitalisation)

#alltests = (startandend,)
#alltests = (variablesconsistent,)
#alltests = (acceleratorsconsistent, variablesconsistent,)
#alltests = (quoteconsistent,)
#alltests = (purepunctuationunchanged,)
#alltests = (escapeconsistent, quoteconsistent, variablesconsistent, acceleratorsconsistent, )
alltests = (untranslated, escapeconsistent, acceleratorsconsistent, variablesconsistent,
            purepunctuationunchanged, simplecapitalisation)
#alltests = (untranslated, purepunctuationunchanged, escapeconsistent,)
#ignoretests = (untranslated,)
#alltests = (untranslated,)
alltests = (translationdifferent,)
ignoretests = ()

# code to actually run the tests (use unittest?)

def runtests(str1, str2, testlist, ignorelist=()):
  """verifies that a number of tests pass for a pair of strings"""
  passed = 1
  for test in ignorelist:
    if not test(str1, str2):
      ignored = 1
  if not ignored:
    for test in testlist:
      if not test(str1, str2):
        if passed:
          passed = 0
          print "failure on strings:\n  %r\n  %r" % (str1, str2)
      print "test %s failed (%s)" % (test.__name__, test.__doc__)
  if not passed: print
  return passed

def batchruntests(pairs, testlist):
  """runs test on a batch of string pairs"""
  passed, numpairs = 0, len(pairs)
  for str1, str2 in pairs:
    passed += runtests(str1, str2, testlist)
  print
  print "total: %d/%d pairs passed" % (passed, numpairs)

if __name__ == '__main__':
  testset = [(r"simple", r"somple"),
             (r"\this equals \that", r"does \this equal \that?"),
             (r"this \'equals\' that", r"this 'equals' that"),
             (r" start and end! they must match.", r"start and end! they must match."),
             (r"check for matching %variables marked like %this", r"%this %variable is marked"),
             (r"check for mismatching %variables marked like %this", r"%that %variable is marked"),
             (r"check for mismatching %variables% too", r"how many %variable% are marked"),
             (r"%% %%", r"%%"),
             (r"Row: %1, Column: %2", r"Mothalo: %1, Kholomo: %2"),
             (r"simple lowercase", r"it is all lowercase"),
             (r"simple lowercase", r"It Is All Lowercase"),
             (r"Simple First Letter Capitals", r"First Letters"),
             (r"SIMPLE CAPITALS", r"First Letters"),
             (r"SIMPLE CAPITALS", r"ALL CAPITALS"),
             (r"forgot to translate", r"  ")
            ]
  batchruntests(testset, alltests)


