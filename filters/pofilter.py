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

"""simple script to run all check filters on gettext .po localization file(s)"""

from translate.storage import po
from translate.filters import checks
from translate.misc import optrecurse
import os

class POChecker(checks.TranslationChecker):
  """allows advanced checks that have access to the whole po element, not just strings"""
  def __init__(self, checkerconfig, excludefilters={}, limitfilters=None, errorhandler=None):
    """construct the POChecker..."""
    super(POChecker, self).__init__(checkerconfig, excludefilters, limitfilters, errorhandler)

  def run_filters(self, thepo):
    """run all the tests in this suite"""
    failures = []
    ignores = []
    functionnames = self.defaultfilters.keys()
    priorityfunctionnames = self.preconditions.keys()
    otherfunctionnames = filter(lambda functionname: functionname not in self.preconditions, functionnames)
    for functionname in priorityfunctionnames + otherfunctionnames:
      if functionname in ignores:
        continue
      filterfunction = getattr(self, functionname)
      if not filterfunction(thepo):
        # we test some preconditions that aren't actually a cause for failure...
        if functionname in self.defaultfilters:
          failures.append("%s: %s" % (functionname, filterfunction.__doc__))
        if functionname in self.preconditions:
          for ignoredfunctionname in self.preconditions[functionname]:
            ignores.append(ignoredfunctionname)
    return failures

class POTeeChecker(checks.TeeChecker):
  """A Checker that can control the POChecker as well as standard checkers"""
  def run_filters(self, thepo, str1, str2):
    """run all the tests in the checker's suites"""
    failures = []
    for checker in self.checkers:
      if isinstance(checker, POChecker):
        failures.extend(checker.run_filters(thepo))
      else:
        failures.extend(checker.run_filters(str1, str2))
    return failures

class StandardPOChecker(POChecker):
  """The standard checks for PO elements"""
  def isfuzzy(self, thepo):
    """check if the po element has been marked fuzzy"""
    return not thepo.isfuzzy()

  def isreview(self, thepo):
    """check if the po element has been marked review"""
    return not thepo.hastypecomment("review")

class pocheckfilter:
  def __init__(self, checkerclasses=None, checkerconfig=None, excludefilters={}, limitfilters=None, includeheader=False, includefuzzy=True, includereview=True):
    """builds a pocheckfilter using the given checker (a list is allowed too)"""
    if checkerclasses is None:
      checkerclasses = [checks.StandardChecker, StandardPOChecker]
    self.checker = POTeeChecker(checkerconfig=checkerconfig, excludefilters=excludefilters, limitfilters=limitfilters, checkerclasses=checkerclasses)
    self.includeheader = includeheader
    self.includefuzzy = includefuzzy
    self.includereview = includereview

  def getfilterdocs(self):
    """lists the docs for filters available on checker..."""
    filterdict = self.checker.getfilters()
    filterdocs = ["%s\t%s" % (name, filterfunc.__doc__) for (name, filterfunc) in filterdict.iteritems()]
    filterdocs.sort()
    return "\n".join(filterdocs)

  def filterelement(self, thepo):
    """runs filters on an element"""
    if thepo.isheader(): return []
    if not self.includefuzzy and thepo.isfuzzy(): return []
    if not self.includereview and thepo.isreview(): return []
    if thepo.hasplural():
      unquotedid = po.getunquotedstr(thepo.msgid, joinwithlinebreak=False)
      unquotedstr = po.getunquotedstr(thepo.msgstr[0], joinwithlinebreak=False)
      failures = self.checker.run_filters(thepo, unquotedid, unquotedstr)
      unquotedid = po.getunquotedstr(thepo.msgid_plural, joinwithlinebreak=False)
      unquotedstr = po.getunquotedstr(thepo.msgstr[1], joinwithlinebreak=False)
      failures += self.checker.run_filters(thepo, unquotedid, unquotedstr)
    else:
      unquotedid = po.getunquotedstr(thepo.msgid, joinwithlinebreak=False)
      unquotedstr = po.getunquotedstr(thepo.msgstr, joinwithlinebreak=False)
      failures = self.checker.run_filters(thepo, unquotedid, unquotedstr)
    return failures

  def filterfile(self, thepofile):
    """runs filters on a file"""
    thenewpofile = po.pofile()
    for thepo in thepofile.poelements:
      failures = self.filterelement(thepo)
      if failures:
        thepo.visiblecomments.extend(["#_ %s\n" % failure for failure in failures])
        thepo.markfuzzy()
        thenewpofile.poelements.append(thepo)
    if self.includeheader and thenewpofile.poelements > 0:
      thenewpofile.poelements.insert(0, thenewpofile.makeheader("UTF-8", "8bit"))
    return thenewpofile

class FilterOptionParser(optrecurse.RecursiveOptionParser):
  """a specialized Option Parser for filter tools..."""
  def __init__(self, formats):
    """construct the specialized Option Parser"""
    optrecurse.RecursiveOptionParser.__init__(self, formats)
    self.set_usage()
    self.add_option("-l", "--listfilters", action="callback", dest='listfilters',
      default=False, callback_kwargs={'dest_value': True},
      callback=self.parse_noinput, help="list filters available")

  def parse_noinput(self, option, opt, value, parser, *args, **kwargs):
    """this sets an option to true, but also sets input to - to prevent an error"""
    setattr(parser.values, option.dest, kwargs['dest_value'])
    parser.values.input = "-"

  def run(self):
    """parses the arguments, and runs recursiveprocess with the resulting options"""
    (options, args) = self.parse_args()
    if options.filterclass is None:
      checkerclasses = [checks.StandardChecker, StandardPOChecker]
    else:
      checkerclasses = [options.filterclass, StandardPOChecker]
    checkerconfig = checks.CheckerConfig()
    if options.notranslatefile:
      if not os.path.exists(options.notranslatefile):
        self.error("notranslatefile %r does not exist" % options.notranslatefile)
      notranslatewords = [line.strip() for line in open(options.notranslatefile).readlines()]
      notranslatewords = dict.fromkeys([key for key in notranslatewords])
      checkerconfig.notranslatewords.update(notranslatewords)
    if options.musttranslatefile:
      if not os.path.exists(options.musttranslatefile):
        self.error("musttranslatefile %r does not exist" % options.musttranslatefile)
      musttranslatewords = [line.strip() for line in open(options.musttranslatefile).readlines()]
      musttranslatewords = dict.fromkeys([key for key in musttranslatewords])
      checkerconfig.musttranslatewords.update(musttranslatewords)
    options.checkfilter = pocheckfilter(checkerclasses, checkerconfig, options.excludefilters, options.limitfilters, options.includeheader, options.includefuzzy, options.includereview)
    if not options.checkfilter.checker.combinedfilters:
      self.error("No valid filters were specified")
    options.inputformats = self.inputformats
    options.outputoptions = self.outputoptions
    self.usepsyco(options)
    if options.listfilters:
      print options.checkfilter.getfilterdocs()
    else:
      self.recursiveprocess(options)

def runpofilter(inputfile, outputfile, templatefile, checkfilter=None):
  """reads in inputfile using po.pofile, filters using pocheckfilter, writes to stdout"""
  fromfile = po.pofile(inputfile)
  tofile = checkfilter.filterfile(fromfile)
  if tofile.isempty():
    return 0
  tolines = tofile.tolines()
  outputfile.writelines(tolines)
  return 1

def main():
  formats = {"po":("po", runpofilter), "pot":("pot", runpofilter), None:("po", runpofilter)}
  parser = FilterOptionParser(formats)
  parser.add_option("", "--review", dest="includereview",
    action="store_true", default=True,
    help="include elements marked for review (default)")
  parser.add_option("", "--noreview", dest="includereview",
    action="store_false", default=True,
    help="exclude elements marked for review")
  parser.add_option("", "--fuzzy", dest="includefuzzy",
    action="store_true", default=True,
    help="include elements marked fuzzy (default)")
  parser.add_option("", "--nofuzzy", dest="includefuzzy",
    action="store_false", default=True,
    help="exclude elements marked fuzzy")
  parser.add_option("", "--header", dest="includeheader",
    action="store_true", default=False,
    help="include a PO header in the output")
  parser.add_option("", "--openoffice", dest="filterclass",
    action="store_const", default=None, const=checks.OpenOfficeChecker,
    help="use the standard checks for OpenOffice translations")
  parser.add_option("", "--mozilla", dest="filterclass",
    action="store_const", default=None, const=checks.MozillaChecker,
    help="use the standard checks for Mozilla translations")
  parser.add_option("", "--gnome", dest="filterclass",
    action="store_const", default=None, const=checks.GnomeChecker,
    help="use the standard checks for Gnome translations")
  parser.add_option("", "--kde", dest="filterclass",
    action="store_const", default=None, const=checks.KdeChecker,
    help="use the standard checks for KDE translations")
  parser.add_option("", "--excludefilter", dest="excludefilters",
    action="append", default=[], type="string", metavar="FILTER",
    help="don't use FILTER when filtering")
  parser.add_option("-t", "--test", dest="limitfilters",
    action="append", default=None, type="string", metavar="FILTER",
    help="only use test FILTERs specified with this option when filtering")
  parser.add_option("", "--notranslatefile", dest="notranslatefile",
    default=None, type="string", metavar="FILE",
    help="read list of untranslatable words from FILE (must not be translated)")
  parser.add_option("", "--musttranslatefile", dest="musttranslatefile",
    default=None, type="string", metavar="FILE",
    help="read list of translatable words from FILE (must be translated)")
  parser.passthrough.append('checkfilter')
  parser.run()

