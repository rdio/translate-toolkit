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

from translate.filters import helpers
from translate.filters import decoration
from translate.filters import prefilters
import sre

# actual test methods

class TranslationChecker(object):
  """Base Checker class which does the checking based on functions available in derived classes"""
  preconditions = {}

  def __init__(self, accelmarkers=[], varmatches=[], excludefilters={}, limitfilters=None):
    """construct the TranslationChecker..."""
    self.setaccelmarkers(accelmarkers)
    self.setvarmatches(varmatches)
    # exclude functions defined in TranslationChecker from being treated as tests...
    self.helperfunctions = {}
    for functionname in dir(TranslationChecker):
      function = getattr(self, functionname)
      if callable(function):
        self.helperfunctions[functionname] = function
    self.defaultfilters = self.getfilters(excludefilters, limitfilters)

  def getfilters(self, excludefilters={}, limitfilters=None):
    """returns dictionary of available filters, including/excluding those in the given lists"""
    filters = {}
    if limitfilters is None:
      # use everything available unless instructed
      limitfilters = dir(self)
    for functionname in limitfilters:
      if functionname in excludefilters: continue
      if functionname in self.helperfunctions: continue
      filterfunction = getattr(self, functionname, None)
      if not callable(filterfunction): continue
      filters[functionname] = filterfunction
    return filters

  def setaccelmarkers(self, accelmarkers):
    """sets the accelerator list"""
    self.accelmarkers = accelmarkers
    self.accfilters = [prefilters.filteraccelerators(accelmarker) for accelmarker in self.accelmarkers]
    self.acccounters = [decoration.countaccelerators(accelmarker) for accelmarker in self.accelmarkers]

  def setvarmatches(self, varmatches):
    """sets the set of start and end markers to match variables by"""
    self.varmatches = varmatches
    self.varfilters =  [prefilters.filtervariables(startmatch, endmatch, prefilters.varname)
                        for startmatch, endmatch in self.varmatches]
    self.varchecks = [decoration.getvariables(startmarker, endmarker)
                      for startmarker, endmarker in self.varmatches]

  def filtervariables(self, str1):
    """filter out variables from str1"""
    return helpers.multifilter(str1, self.varfilters)

  def filteraccelerators(self, str1):
    """filter out accelerators from str1"""
    return helpers.multifilter(str1, self.accfilters)

  def filterwordswithpunctuation(self, str1):
    """replaces words with punctuation with their unpunctuated equivalents..."""
    return prefilters.filterwordswithpunctuation(str1)

  def run_filters(self, str1, str2):
    """run all the tests in this suite"""
    failures = []
    ignores = []
    functionnames = self.defaultfilters.keys()
    priorityfunctionnames = self.preconditions.keys()
    otherfunctionnames = filter(lambda functionname: functionname not in self.preconditions, functionnames)
    for functionname in priorityfunctionnames + otherfunctionnames:
      if functionname in ignores:
        continue
      filterfunction = getattr(self, functionname, None)
      # this filterfunction may only be defined on another checker if using TeeChecker
      if filterfunction is None:
        continue
      if not filterfunction(str1, str2):
        # we test some preconditions that aren't actually a cause for failure...
        if functionname in self.defaultfilters:
          failures.append("%s: %s" % (functionname, filterfunction.__doc__))
        if functionname in self.preconditions:
          for ignoredfunctionname in self.preconditions[functionname]:
            ignores.append(ignoredfunctionname)
    return failures

class TeeChecker:
  """A Checker that controls multiple checkers..."""
  def __init__(self, accelmarkers=[], varmatches=[], excludefilters={}, limitfilters=None, checkerclasses=None):
    """construct a TeeChecker from the given checkers"""
    self.limitfilters = limitfilters
    if checkerclasses is None:
      checkerclasses = [StandardChecker]
    self.checkers = [checkerclass(excludefilters=excludefilters, limitfilters=limitfilters) for checkerclass in checkerclasses]
    self.combinedfilters = self.getfilters(excludefilters, limitfilters)

  def getfilters(self, excludefilters={}, limitfilters=None):
    """returns dictionary of available filters, including/excluding those in the given lists"""
    filterslist = [checker.getfilters(excludefilters, limitfilters) for checker in self.checkers]
    self.combinedfilters = {}
    for filters in filterslist:
      self.combinedfilters.update(filters)
    # TODO: move this somewhere more sensible (a checkfilters method?)
    if limitfilters is not None:
      for filtername in limitfilters:
        if not filtername in self.combinedfilters:
          import sys
          print >>sys.stderr, "warning: could not find filter %s" % filtername
    return self.combinedfilters

  def run_filters(self, str1, str2):
    """run all the tests in the checker's suites"""
    failures = []
    for checker in self.checkers:
      failures.extend(checker.run_filters(str1, str2))
    return failures

class StandardChecker(TranslationChecker):
  """simply defines a bunch of tests..."""
  def untranslated(self, str1, str2):
    """checks whether a string has been translated at all"""
    return not (len(str1.strip()) > 0 and len(str2) == 0)

  def unchanged(self, str1, str2):
    """checks whether a translation is basically identical to the original string"""
    str1 = self.filteraccelerators(str1)
    str2 = self.filteraccelerators(str2)
    return (str1.isdigit() or len(str1) < 2) or (str1.strip().lower() != str2.strip().lower())

  def blank(self, str1, str2):
    """checks whether a translation is totally blank"""
    len1 = len(prefilters.removekdecomments(str1).strip())
    len2 = len(str2.strip())
    return not (len1 > 0 and len(str2) != 0 and len2 == 0)

  def short(self, str1, str2):
    """checks whether a translation is much shorter than the original string"""
    len1 = len(prefilters.removekdecomments(str1).strip())
    len2 = len(str2.strip())
    return not ((len1 > 0) and (0 < len2 < (len1 * 0.1)))

  def long(self, str1, str2):
    """checks whether a translation is much longer than the original string"""
    len1 = len(prefilters.removekdecomments(str1).strip())
    len2 = len(str2.strip())
    return not ((len1 > 0) and (0 < len1 < (len2 * 0.1)))

  def escapes(self, str1, str2):
    """checks whether escaping is consistent between the two strings"""
    return helpers.countsmatch(prefilters.removekdecomments(str1), str2, ("\\", "\\\\"))

  def singlequoting(self, str1, str2):
    """checks whether singlequoting is consistent between the two strings"""
    str1 = self.filteraccelerators(self.filtervariables(self.filterwordswithpunctuation(str1)))
    str2 = self.filteraccelerators(self.filtervariables(self.filterwordswithpunctuation(str2)))
    return helpers.countsmatch(str1, str2, ("'", "''", "\\'"))

  def doublequoting(self, str1, str2):
    """checks whether doublequoting is consistent between the two strings"""
    str1 = self.filteraccelerators(self.filtervariables(str1))
    str2 = self.filteraccelerators(self.filtervariables(str2))
    return helpers.countsmatch(str1, str2, ('"', '""', '\\"'))

  def doublespacing(self, str1, str2):
    """checks for bad double-spaces by comparing to original"""
    str1 = self.filteraccelerators(self.filtervariables(str1))
    str2 = self.filteraccelerators(self.filtervariables(str2))
    return helpers.countmatch(str1, str2, "  ")

  def puncspacing(self, str1, str2):
    """checks for bad spacing after punctuation"""
    str1 = self.filteraccelerators(self.filtervariables(str1))
    str2 = self.filteraccelerators(self.filtervariables(str2))
    for puncchar in ",.?!:;":
      plaincount1 = str1.count(puncchar)
      plaincount2 = str2.count(puncchar)
      spacecount1 = str1.count(puncchar+" ")
      spacecount2 = str2.count(puncchar+" ")
      if plaincount1 == plaincount2 and spacecount1 != spacecount2:
        # handle extra spaces that are because of transposed punctuation
        if str1.endswith(puncchar) != str2.endswith(puncchar) and abs(spacecount1-spacecount2) == 1:
          continue
        return 0
    return 1

  def accelerators(self, str1, str2):
    """checks whether accelerators are consistent between the two strings"""
    str1 = self.filtervariables(str1)
    str2 = self.filtervariables(str2)
    return helpers.funcsmatch(str1, str2, self.acccounters)

  def variables(self, str1, str2):
    """checks whether variables of various forms are consistent between the two strings"""
    return helpers.funcsmatch(str1, str2, self.varchecks)

  def numbers(self, str1, str2):
    """checks whether numbers of various forms are consistent between the two strings"""
    return helpers.funcmatch(str1, str2, decoration.getnumbers)

  def startwhitespace(self, str1, str2):
    """checks whether whitespace at the beginning of the strings matches"""
    str1 = self.filteraccelerators(self.filtervariables(str1))
    str2 = self.filteraccelerators(self.filtervariables(str2))
    return helpers.funcmatch(str1, str2, decoration.spacestart)

  def endwhitespace(self, str1, str2):
    """checks whether whitespace at the end of the strings matches"""
    str1 = self.filteraccelerators(self.filtervariables(str1))
    str2 = self.filteraccelerators(self.filtervariables(str2))
    return helpers.funcmatch(str1, str2, decoration.spaceend)

  def startpunc(self, str1, str2):
    """checks whether punctuation at the beginning of the strings match"""
    str1 = self.filteraccelerators(self.filtervariables(self.filterwordswithpunctuation(str1)))
    str2 = self.filteraccelerators(self.filtervariables(self.filterwordswithpunctuation(str2)))
    return helpers.funcmatch(str1, str2, decoration.puncstart)

  def endpunc(self, str1, str2):
    """checks whether punctuation at the end of the strings match"""
    str1 = self.filteraccelerators(self.filtervariables(self.filterwordswithpunctuation(str1)))
    str2 = self.filteraccelerators(self.filtervariables(self.filterwordswithpunctuation(str2)))
    return helpers.funcmatch(str1, str2, decoration.puncend)

  def purepunc(self, str1, str2):
    """checks that strings that are purely punctuation are not changed"""
    # this test is a subset of startandend
    if (decoration.ispurepunctuation(str1)):
      return str1 == str2
    return 1

  def brackets(self, str1, str2):
    """checks that the number of brackets in both strings match"""
    str1 = self.filtervariables(prefilters.removekdecomments(str1))
    str2 = self.filtervariables(str2)
    return helpers.countsmatch(str1, str2, ("[", "]", "{", "}", "(", ")"))

  def sentencecount(self, str1, str2):
    """checks that the number of sentences in both strings match"""
    return helpers.countsmatch(prefilters.removekdecomments(str1), str2, ".")

  def simplecaps(self, str1, str2):
    """checks the capitalisation of two strings isn't wildly different"""
    capitals1, capitals2 = helpers.filtercount(str1, type(str1).isupper), helpers.filtercount(str2, type(str2).isupper)
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

  def acronyms(self, str1, str2):
    """checks that acronyms that appear are unchanged"""
    for word in self.filteraccelerators(self.filtervariables(str1)).split():
      word = word.strip(":;.,()'\"")
      if word.isupper() and len(word) > 1:
        if self.filteraccelerators(self.filtervariables(str2)).find(word) == -1:
	  return False
    return True

  def filepaths(self, str1, str2):
    """checks that file paths have not been translated"""
    for word1 in self.filteraccelerators(str1).split():
      if word1.startswith("/"):
        if not helpers.countsmatch(str1, str2, (word1,)):
          return False
    return True

  def xmltags(self, str1, str2):
    """checks that XML/HTML tags have not been translated"""
    str1 = prefilters.removekdecomments(str1)
    tags = sre.findall("<[^>]+>", str1)
    # TODO break down translatable tags eg <img alt="blah">
    if len(tags) == 1 and len(tags[0]) == len(str1):
      return True
    return helpers.countsmatch(str1, str2, tags)

  def kdecomments(self, str1, str2):
    """checks to ensure that no KDE style comments appear in the translation"""
    return str2.find("\n_:") == -1 and not str2.startswith("_:")

  def compendiumconflicts(self, str1, str2):
    """checks for Gettext compendium conflicts (#-#-#-#-#)"""
    return str2.find("#-#-#-#-#") == -1

  preconditions = {"untranslated": ("escapes", "short", "long", "unchanged", "singlequoting", "doublequoting",
                                    "accelerators", "variables", "numbers",
                                    "doublespacing", "puncspacing", "startwhitespace", "endwhitespace",
                                    "startpunc", "endpunc", "purepunc", "simplecaps", "acronyms", "brackets", "xmltags") }

# code to actually run the tests (use unittest?)

class OpenOfficeChecker(StandardChecker):
  def __init__(self, **kwargs):
    StandardChecker.__init__(self,
      accelmarkers = ("~"),
      varmatches = (("&", ";"), ("%", "%"), ("%", None), ("$(", ")"), ("$", "$"), ("${", "}"), ("#", "#")),
      **kwargs
      )

class MozillaChecker(StandardChecker):
  def __init__(self, **kwargs):
    StandardChecker.__init__(self,
      accelmarkers = ("&"),
      varmatches = (("&", ";"), ("%", "%"), ("%", 1), ("$", None), ("#", 1)),
      **kwargs
      )

class GnomeChecker(StandardChecker):
  def __init__(self, **kwargs):
    StandardChecker.__init__(self,
      accelmarkers = ("_"),
      varmatches = (("%", 1), ("$(", ")")),
      **kwargs
      )

class KdeChecker(StandardChecker):
  def __init__(self, **kwargs):
	# TODO allow setup of KDE plural and translator comments so that they do
	# not create false postives
    StandardChecker.__init__(self,
      accelmarkers = ("&"),
      varmatches = (("%", 1),),
      **kwargs
      )

projectcheckers = {
  "openoffice": OpenOfficeChecker,
  "mozilla": MozillaChecker,
  "kde": KdeChecker,
  "gnome": GnomeChecker
  }

def runtests(str1, str2, ignorelist=()):
  """verifies that the tests pass for a pair of strings"""
  checker = StandardChecker(excludefilters=ignorelist)
  failures = checker.run_filters(str1, str2)
  for failure in failures:
    print "failure: %s\n  %r\n  %r" % (failure, str1, str2)
  return failures

def batchruntests(pairs):
  """runs test on a batch of string pairs"""
  passed, numpairs = 0, len(pairs)
  for str1, str2 in pairs:
    if runtests(str1, str2):
      passed += 1
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
  batchruntests(testset)


