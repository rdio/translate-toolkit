#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
try:
  from enchant import checker
  checkers = {}
  def dospellcheck(text, lang):
    if lang in checkers:
      c = checkers[lang]
    else:
      checkers[lang] = checker.SpellChecker(lang)
      c = checkers[lang]
    c.set_text(text)
    for err in c:
      yield err.word, err.wordpos, err.suggest()
except ImportError:
  try:
    from jToolkit import spellcheck
    dospellcheck = spellcheck.check
  except ImportError:
    def dospellcheck(text, lang):
      return []

# actual test methods

class FilterFailure(Exception):
  """This exception signals that a Filter didn't pass, and gives an explanation / comment"""
  def __init__(self, messages):
    if not isinstance(messages, list):
      messages = [messages]
    strmessages = []
    for message in messages:
      if isinstance(message, unicode):
        message = message.encode("utf-8")
      strmessages.append(message)
    messages = ", ".join(strmessages)
    Exception.__init__(self, messages)

class SeriousFilterFailure(FilterFailure):
  """This exception signals that a Filter didn't pass, and the bad translation might break an application (so the string will be marked fuzzy)"""
  pass

def passes(filterfunction, str1, str2):
  """returns whether the given strings pass on the given test, handling FilterFailures"""
  try:
    filterresult = filterfunction(str1, str2)
  except FilterFailure, e:
    filterresult = False
  return filterresult

def fails(filterfunction, str1, str2):
  """returns whether the given strings fail on the given test, handling FilterFailures"""
  try:
    filterresult = filterfunction(str1, str2)
  except FilterFailure, e:
    filterresult = False
  return not filterresult

class CheckerConfig(object):
  """object representing the configuration of a checker"""
  def __init__(self, targetlanguage=None, accelmarkers=None, varmatches=None, notranslatewords=None, musttranslatewords=None, validchars=None):
    # make sure that we initialise empty lists properly (default arguments get reused!)
    if accelmarkers is None:
      accelmarkers = []
    if varmatches is None:
      varmatches = []
    if musttranslatewords is None:
      musttranslatewords = []
    if notranslatewords is None:
      notranslatewords = []
    self.targetlanguage = targetlanguage
    self.accelmarkers = accelmarkers
    self.varmatches = varmatches
    # TODO: allow user configuration of untranslatable words
    self.notranslatewords = dict.fromkeys([key for key in notranslatewords])
    self.musttranslatewords = dict.fromkeys([key for key in musttranslatewords])
    if isinstance(validchars, str):
      validchars = validchars.decode("utf-8")
    self.validcharsmap = {}
    self.updatevalidchars(validchars)
  def update(self, otherconfig):
    """combines the info in otherconfig into this config object"""
    self.targetlanguage = otherconfig.targetlanguage or self.targetlanguage
    self.accelmarkers.extend(otherconfig.accelmarkers)
    self.varmatches.extend(otherconfig.varmatches)
    self.notranslatewords.update(otherconfig.notranslatewords)
    self.musttranslatewords.update(otherconfig.musttranslatewords)
    self.validcharsmap.update(otherconfig.validcharsmap)
  def updatevalidchars(self, validchars):
    """updates the map that eliminates valid characters"""
    if validchars is None:
      return True
    validcharsmap = dict([(ord(validchar), None) for validchar in validchars])
    self.validcharsmap.update(validcharsmap)

class TranslationChecker(object):
  """Base Checker class which does the checking based on functions available in derived classes"""
  preconditions = {}

  def __init__(self, checkerconfig=None, excludefilters=None, limitfilters=None, errorhandler=None):
    """construct the TranslationChecker..."""
    self.errorhandler = errorhandler
    if checkerconfig is None:
      self.setconfig(CheckerConfig())
    else:
      self.setconfig(checkerconfig)
    # exclude functions defined in TranslationChecker from being treated as tests...
    self.helperfunctions = {}
    for functionname in dir(TranslationChecker):
      function = getattr(self, functionname)
      if callable(function):
        self.helperfunctions[functionname] = function
    self.defaultfilters = self.getfilters(excludefilters, limitfilters)

  def getfilters(self, excludefilters=None, limitfilters=None):
    """returns dictionary of available filters, including/excluding those in the given lists"""
    filters = {}
    if limitfilters is None:
      # use everything available unless instructed
      limitfilters = dir(self)
    if excludefilters is None:
      excludefilters = {}
    for functionname in limitfilters:
      if functionname in excludefilters: continue
      if functionname in self.helperfunctions: continue
      if functionname == "errorhandler": continue
      filterfunction = getattr(self, functionname, None)
      if not callable(filterfunction): continue
      filters[functionname] = filterfunction
    return filters

  def setconfig(self, config):
    """sets the accelerator list"""
    self.config = config
    self.accfilters = [prefilters.filteraccelerators(accelmarker) for accelmarker in self.config.accelmarkers]
    self.varfilters =  [prefilters.filtervariables(startmatch, endmatch, prefilters.varname)
                        for startmatch, endmatch in self.config.varmatches]

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
    """run all the tests in this suite, return failures as testname, message_or_exception"""
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
      filtermessage = filterfunction.__doc__
      try:
        filterresult = filterfunction(str1, str2)
      except FilterFailure, e:
        filterresult = False
        filtermessage = e
      except Exception, e:
        if self.errorhandler is None:
          raise
          raise ValueError("error in filter %s: %r, %r, %s" % (functionname, str1, str2, e))
        else:
          filterresult = self.errorhandler(functionname, str1, str2, e)
      if not filterresult:
        # we test some preconditions that aren't actually a cause for failure...
        if functionname in self.defaultfilters:
          failures.append((functionname, filtermessage))
        if functionname in self.preconditions:
          for ignoredfunctionname in self.preconditions[functionname]:
            ignores.append(ignoredfunctionname)
    return failures

class TeeChecker:
  """A Checker that controls multiple checkers..."""
  def __init__(self, checkerconfig=None, excludefilters=None, limitfilters=None, checkerclasses=None, errorhandler=None):
    """construct a TeeChecker from the given checkers"""
    self.limitfilters = limitfilters
    if checkerclasses is None:
      checkerclasses = [StandardChecker]
    self.checkers = [checkerclass(checkerconfig=checkerconfig, excludefilters=excludefilters, limitfilters=limitfilters, errorhandler=errorhandler) for checkerclass in checkerclasses]
    self.combinedfilters = self.getfilters(excludefilters, limitfilters)

  def getfilters(self, excludefilters=None, limitfilters=None):
    """returns dictionary of available filters, including/excluding those in the given lists"""
    if excludefilters is None:
      excluefilters = {}
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
    str1 = self.filteraccelerators(prefilters.removekdecomments(str1))
    str2 = self.filteraccelerators(str2)
    if not (str1.isdigit() or len(str1) < 2) and (str1.strip().lower() == str2.strip().lower()):
      raise FilterFailure("please translate")
    return True

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
    str1 = prefilters.removekdecomments(str1)
    if not helpers.countsmatch(str1, str2, ("\\", "\\\\")):
      escapes1 = ", ".join(["'%s'" % word for word in str1.split() if "\\" in word])
      escapes2 = ", ".join(["'%s'" % word for word in str2.split() if "\\" in word])
      raise SeriousFilterFailure("escapes in original (%s) don't match escapes in translation (%s)" % (escapes1, escapes2))
    else:
      return True

  def singlequoting(self, str1, str2):
    """checks whether singlequoting is consistent between the two strings"""
    str1 = self.filteraccelerators(self.filtervariables(self.filterwordswithpunctuation(prefilters.removekdecomments(str1))))
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
    messages = []
    for accelmarker in self.config.accelmarkers:
      counter = decoration.countaccelerators(accelmarker)
      count1 = counter(str1)
      count2 = counter(str2)
      if count1 == count2:
        continue
      if count1 == 1 and count2 == 0:
        messages.append("accelerator %s is missing from translation" % accelmarker)
      elif count1 == 0:
        messages.append("accelerator %s does not occur in original and should not be in translation" % accelmarker)
      elif count1 == 1 and count2 > count1:
        messages.append("accelerator %s is repeated in translation" % accelmarker)
      else:
        messages.append("accelerator %s occurs %d time(s) in original and %d time(s) in translation" % (accelmarker, count1, count2))
    if messages:
      raise FilterFailure(messages)
    return True

  def variables(self, str1, str2):
    """checks whether variables of various forms are consistent between the two strings"""
    messages = []
    mismatch1, mismatch2 = [], []
    varnames1, varnames2 = [], []
    for startmarker, endmarker in self.config.varmatches:
      varchecker = decoration.getvariables(startmarker, endmarker)
      if startmarker and endmarker:
        if isinstance(endmarker, int):
          redecorate = lambda var: startmarker + var
        else:
          redecorate = lambda var: startmarker + var + endmarker
      elif startmarker:
        redecorate = lambda var: startmarker + var
      else:
        redecorate = lambda var: var
      vars1 = varchecker(str1)
      vars2 = varchecker(str2)
      if vars1 != vars2:
        vars1, vars2 = [var for var in vars1 if var not in vars2], [var for var in vars2 if var not in vars1]
        # filter variable names we've already seen, so they aren't matched by more than one filter...
        vars1, vars2 = [var for var in vars1 if var not in varnames1], [var for var in vars2 if var not in varnames2]
        varnames1.extend(vars1)
        varnames2.extend(vars2)
        vars1 = map(redecorate, vars1)
        vars2 = map(redecorate, vars2)
        mismatch1.extend(vars1)
        mismatch2.extend(vars2)
    if mismatch1:
      messages.append("do not translate: %s" % ", ".join(mismatch1))
    elif mismatch2:
      messages.append("translation contains variables not in original: %s" % ", ".join(mismatch2))
    if messages and mismatch1:
      raise SeriousFilterFailure(messages)
    elif messages:
      raise FilterFailure(messages)
    return True

  def functions(self, str1, str2):
    """checks to see that function names are not translated"""
    return helpers.funcmatch(str1, str2, decoration.getfunctions)

  def emails(self, str1, str2):
    """checks to see that emails are not translated"""
    return helpers.funcmatch(str1, str2, decoration.getemails)

  def urls(self, str1, str2):
    """checks to see that URLs are not translated"""
    return helpers.funcmatch(str1, str2, decoration.geturls)

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
    messages = []
    missing = []
    extra = []
    for bracket in ("[", "]", "{", "}", "(", ")"):
      count1 = str1.count(bracket)
      count2 = str2.count(bracket)
      if count2 < count1:
        missing.append("'%s'" % bracket)
      elif count2 > count1:
        extra.append("'%s'" % bracket)
    if missing:
      messages.append("translation is missing %s" % ", ".join(missing))
    if extra:
      messages.append("translation has extra %s" % ", ".join(extra))
    if messages:
      raise FilterFailure(messages)
    return True

  def sentencecount(self, str1, str2):
    """checks that the number of sentences in both strings match"""
    return helpers.countsmatch(prefilters.removekdecomments(str1), str2, ".")

  def startcaps(self, str1, str2):
    """checks that the message starts with the correct capitalisation"""
    punc = "\\.,/?!`'\"[]{}()@#$%^&*_-;:<>"
    str1 = self.filteraccelerators(self.filtervariables(prefilters.removekdecomments(str1))).lstrip().lstrip(punc)
    str2 = self.filteraccelerators(self.filtervariables(str2)).lstrip().lstrip(punc)
    if len(str1) > 1 and len(str2) > 1:
      return str1[0].isupper() == str2[0].isupper()
    if len(str1) == 0 and len(str2) == 0:
      return True
    if len(str1) == 0 or len(str2) == 0:
      return False
    return True

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
    acronyms = []
    vars1 = []
    for startmatch, endmatch in self.config.varmatches:
      vars1 += decoration.getvariables(startmatch, endmatch)(str1)
    for word in self.filteraccelerators(self.filtervariables(str1)).split():
      word = word.strip(":;.,()'\"")
      if word.isupper() and len(word) > 1 and word not in vars1:
        if self.filteraccelerators(self.filtervariables(str2)).find(word) == -1:
	  acronyms.append(word)
    if acronyms:
      raise FilterFailure("acronyms should not be translated: " + ", ".join(acronyms))
    return True

  def doublewords(self, str1, str2):
    """checks for repeated words in the translation"""
    lastword = ""
    without_newlines = "\n".join(str2.split("\n"))
    words = self.filteraccelerators(self.filtervariables(without_newlines)).replace(".", "").lower().split()
    for word in words:
      if word == lastword:
        return False
      lastword = word
    return True

  def notranslatewords(self, str1, str2):
    """checks that words configured as untranslatable appear in the translation too"""
    if not self.config.notranslatewords:
      return True
    words1 = self.filteraccelerators(self.filtervariables(str1)).replace(".", " ").split()
    words2 = self.filteraccelerators(self.filtervariables(str2)).replace(".", " ").split()
    stopwords = [word for word in words1 if word in self.config.notranslatewords and word not in words2]
    if stopwords:
      raise FilterFailure("do not translate: %s" % (", ".join(stopwords)))
    return True

  def musttranslatewords(self, str1, str2):
    """checks that words configured as definitely translatable don't appear in the translation"""
    if not self.config.musttranslatewords:
      return True
    words1 = self.filteraccelerators(self.filtervariables(str1)).replace(".", " ").split()
    words2 = self.filteraccelerators(self.filtervariables(str2)).replace(".", " ").split()
    stopwords = [word for word in words1 if word in self.config.musttranslatewords and word in words2]
    if stopwords:
      raise FilterFailure("please translate: %s" % (", ".join(stopwords)))
    return True

  def validchars(self, str1, str2):
    """checks that only characters specified as valid appear in the translation"""
    if not self.config.validcharsmap:
      return True
    if isinstance(str1, str):
      str1 = str1.decode('utf-8')
    if isinstance(str2, str):
      str2 = str2.decode('utf-8')
    invalid1 = str1.translate(self.config.validcharsmap)
    invalid2 = str2.translate(self.config.validcharsmap)
    invalidchars = ["'%s' (\\u%04x)" % (invalidchar.encode('utf-8'), ord(invalidchar)) for invalidchar in invalid2 if invalidchar not in invalid1]
    if invalidchars:
      raise FilterFailure("invalid chars: %s" % (", ".join(invalidchars)))
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

  def spellcheck(self, str1, str2):
    """checks words that don't pass a spell check"""
    if not self.config.targetlanguage:
      return True
    str1 = self.filteraccelerators(self.filtervariables(str1))
    str2 = self.filteraccelerators(self.filtervariables(str2))
    ignore1 = []
    messages = []
    for word, index, suggestions in dospellcheck(str1, lang="en"):
      ignore1.append(word)
    for word, index, suggestions in dospellcheck(str2, lang=self.config.targetlanguage):
      if word in ignore1:
        continue
      # hack to ignore hyphenisation rules
      if word in suggestions:
        continue
      messages.append(u"check spelling of %s (could be %s)" % (word, u" / ".join(suggestions)))
    if messages:
      raise FilterFailure(messages)
    return True

  preconditions = {"untranslated": ("simplecaps", "variables", "startcaps",
                                    "accelerators", "brackets", "endpunc",
                                    "acronyms", "xmltags", "startpunc",
                                    "endwhitespace", "startwhitespace",
                                    "escapes", "doublequoting", "singlequoting", 
                                    "filepaths", "purepunc", "doublespacing",
                                    "sentencecount", "numbers", "isfuzzy",
                                    "isreview", "notranslatewords", "musttranslatewords"),
                   "compendiumconflicts": ("accelerators", "brackets", "escapes", 
                                    "numbers", "startpunc", "long", "variables", 
                                    "startcaps", "sentencecount", "simplecaps",
                                    "doublespacing", "endpunc", "xmltags",
                                    "startwhitespace", "endwhitespace",
                                    "singlequoting", "doublequoting",
                                    "filepaths", "purepunc", "doublewords") }

# code to actually run the tests (use unittest?)

openofficeconfig = CheckerConfig(
  accelmarkers = ("~"),
  varmatches = (("&", ";"), ("%", "%"), ("%", None), ("$(", ")"), ("$", "$"), ("${", "}"), ("#", "#"), ("($", ")"), ("$[", "]"), ("[", "]"), ("$", None))
  )

class OpenOfficeChecker(StandardChecker):
  def __init__(self, **kwargs):
    checkerconfig = kwargs.get("checkerconfig", None)
    if checkerconfig is None:
      checkerconfig = CheckerConfig()
      kwargs["checkerconfig"] = checkerconfig
    checkerconfig.update(openofficeconfig)
    StandardChecker.__init__(self, **kwargs)

mozillaconfig = CheckerConfig(
  accelmarkers = ("&"),
  varmatches = (("&", ";"), ("%", "%"), ("%", 1), ("$", None), ("#", 1))
  )

class MozillaChecker(StandardChecker):
  def __init__(self, **kwargs):
    checkerconfig = kwargs.get("checkerconfig", None)
    if checkerconfig is None:
      checkerconfig = CheckerConfig()
      kwargs["checkerconfig"] = checkerconfig
    checkerconfig.update(mozillaconfig)
    StandardChecker.__init__(self, **kwargs)

gnomeconfig = CheckerConfig(
  accelmarkers = ("_"),
  varmatches = (("%", 1), ("$(", ")"))
  )

class GnomeChecker(StandardChecker):
  def __init__(self, **kwargs):
    checkerconfig = kwargs.get("checkerconfig", None)
    if checkerconfig is None:
      checkerconfig = CheckerConfig()
      kwargs["checkerconfig"] = checkerconfig
    checkerconfig.update(gnomeconfig)
    StandardChecker.__init__(self, **kwargs)

kdeconfig = CheckerConfig(
  accelmarkers = ("&"),
  varmatches = (("%", 1),)
  )

class KdeChecker(StandardChecker):
  def __init__(self, **kwargs):
	# TODO allow setup of KDE plural and translator comments so that they do
	# not create false postives
    checkerconfig = kwargs.get("checkerconfig", None)
    if checkerconfig is None:
      checkerconfig = CheckerConfig()
      kwargs["checkerconfig"] = checkerconfig
    checkerconfig.update(kdeconfig)
    StandardChecker.__init__(self, **kwargs)

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
  for testname, message in failures:
    print "failure: %s: %s\n  %r\n  %r" % (testname, message, str1, str2)
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


