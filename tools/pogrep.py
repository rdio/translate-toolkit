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

"""grep for gettext .po localization files"""

from translate.storage import po
from translate.misc import optrecurse
import sre

class pogrepfilter:
  def __init__(self, searchstring, searchparts, ignorecase=False, useregexp=False, invertmatch=False, accelchar=None):
    """builds a pocheckfilter using the given checker"""
    self.searchstring = searchstring.decode('utf-8')
    if searchparts:
      self.searchmsgid = "msgid" in searchparts
      self.searchmsgstr = "msgstr" in searchparts
    else:
      self.searchmsgid = True
      self.searchmsgstr = True
    self.ignorecase = ignorecase
    if self.ignorecase:
      self.searchstring = self.searchstring.lower()
    self.useregexp = useregexp
    if self.useregexp:
      self.searchpattern = sre.compile(self.searchstring)
    self.invertmatch = invertmatch
    self.accelchar = accelchar

  def matches(self, teststr):
    if self.ignorecase:
      teststr = teststr.lower()
    if self.accelchar:
      teststr = sre.sub(self.accelchar + self.accelchar, "#", teststr)
      teststr = sre.sub(self.accelchar, "", teststr)
    if self.useregexp:
      found = self.searchpattern.search(teststr)
    else:
      found = teststr.find(self.searchstring) != -1
    if self.invertmatch:
      found = not found
    return found

  def filterelement(self, thepo):
    """runs filters on an element"""
    if thepo.isheader(): return []
    if thepo.hasplural():
      if self.searchmsgid:
        unquotedid = po.getunquotedstr(thepo.msgid)
        unquotedid_plural = po.getunquotedstr(thepo.msgid_plural)
        if self.matches(unquotedid) or self.matches(unquotedid_plural):
          return True
      if self.searchmsgstr:
        if isinstance(thepo.msgstr, dict):
          for msgstr in thepo.msgstr.values():
            unquotedstr = po.getunquotedstr(msgstr)
            if self.matches(unquotedstr): return True
        else:
          unquotedstr = po.getunquotedstr(thepo.msgstr)
          if self.matches(unquotedstr): return True
    else:
      if self.searchmsgid:
        unquotedid = po.getunquotedstr(thepo.msgid)
        if self.matches(unquotedid): return True
      if self.searchmsgstr:
        unquotedstr = po.getunquotedstr(thepo.msgstr)
        if self.matches(unquotedstr): return True
    return False

  def filterfile(self, thepofile):
    """runs filters on a file"""
    thenewpofile = po.pofile()
    for thepo in thepofile.poelements:
      matches = self.filterelement(thepo)
      if matches:
        thenewpofile.poelements.append(thepo)
    return thenewpofile

class GrepOptionParser(optrecurse.RecursiveOptionParser):
  """a specialized Option Parser for the grep tool..."""
  def parse_args(self, args=None, values=None):
    """parses the command line options, handling implicit input/output args"""
    (options, args) = optrecurse.optparse.OptionParser.parse_args(self, args, values)
    # some intelligence as to what reasonable people might give on the command line
    if args:
      options.searchstring = args[0]
      args = args[1:]
    else:
      self.error("At least one argument must be given for the search string")
    if args and not options.input:
      if not options.output:
        options.input = args[:-1]
        args = args[-1:]
      else:
        options.input = args
        args = []
    if args and not options.output:
      options.output = args[-1]
      args = args[:-1]
    if args:
      self.error("You have used an invalid combination of --input, --output and freestanding args")
    if isinstance(options.input, list) and len(options.input) == 1:
      options.input = options.input[0]
    return (options, args)

  def set_usage(self, usage=None):
    """sets the usage string - if usage not given, uses getusagestring for each option"""
    if usage is None:
      self.usage = "%prog searchstring " + " ".join([self.getusagestring(option) for option in self.option_list])
    else:
      super(GrepOptionParser, self).set_usage(usage)

  def run(self):
    """parses the arguments, and runs recursiveprocess with the resulting options"""
    (options, args) = self.parse_args()
    options.inputformats = self.inputformats
    options.outputoptions = self.outputoptions
    options.checkfilter = pogrepfilter(options.searchstring, options.searchparts, options.ignorecase, options.useregexp, options.invertmatch, options.accelchar)
    self.usepsyco(options)
    self.recursiveprocess(options)

def runpogrep(inputfile, outputfile, templatefile, checkfilter):
  """reads in inputfile using po.pofile, filters using pocheckfilter, writes to stdout"""
  fromfile = po.pofile(inputfile)
  tofile = checkfilter.filterfile(fromfile)
  if tofile.isempty():
    return 0
  outputfile.write(str(tofile))
  return 1

def main():
  formats = {"po":("po", runpogrep), "pot":("pot", runpogrep), None:("po", runpogrep)}
  parser = GrepOptionParser(formats)
  parser.add_option("", "--search", dest="searchparts",
    action="append", type="choice", choices=["msgid", "msgstr"],
    metavar="SEARCHPARTS", help="searches the given parts")
  parser.add_option("-I", "--ignore-case", dest="ignorecase",
    action="store_true", default=False, help="ignore case distinctions")
  parser.add_option("-e", "--regexp", dest="useregexp",
    action="store_true", default=False, help="use regular expression matching")
  parser.add_option("-v", "--invert-match", dest="invertmatch",
    action="store_true", default=False, help="select non-matching lines")
  parser.add_option("", "--accelerator", dest="accelchar",
    action="store", type="choice", choices=["&", "_", "~"],
    metavar="ACCELERATOR", help="ignores the given accelerator when matching")
  parser.set_usage()
  parser.passthrough.append('checkfilter')
  parser.run()

