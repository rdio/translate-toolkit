#!/usr/bin/env python
#
# Copyright 2002-2004 Zuza Software Foundation
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
#

"""script to convert an OpenOffice exported .oo localization format to a
gettext .po localization file using the po and oo modules, and the 
oo2po convertor class which is in this module
You can convert back to .oo using po2oo.py"""

import sys
import os
from translate.storage import po
from translate.storage import oo
from translate.misc import quote

class oo2po:
  def __init__(self, languages=None, blankmsgstr=0):
    """construct an oo2po converter for the specified languages"""
    # languages is a pair of language ids
    self.languages = languages
    self.blankmsgstr = blankmsgstr

  def makepo(self, part1, part2, key, subkey):
    """makes a po element out of a subkey of two parts"""
    thepo = po.poelement()
    thepo.sourcecomments.append("#: " + key + "." + subkey + "\n")
    text1 = getattr(part1, subkey)
    text2 = getattr(part2, subkey)
    thepo.msgid = [quote.quotestr(line) for line in text1.split('\n')]
    thepo.msgstr = [quote.quotestr(line) for line in text2.split('\n')]
    return thepo

  def makekey(self, ookey):
    """converts an oo key tuple into a key identifier for the po file"""
    project, sourcefile, resourcetype, groupid, localid, platform = ookey
    sourcefile = sourcefile.replace('\\','/')
    if len(groupid) == 0 or len(localid) == 0:
      id = groupid + localid
    else:
      id = groupid + "." + localid
    key = "%s/%s#%s" % (project, sourcefile, id)
    return oo.normalizefilename(key)

  def convertelement(self, theoo):
    """convert an oo element into a list of po elements"""
    if self.blankmsgstr:
      if self.languages is None:
        part1 = theoo.lines[0]
      else:
        part1 = theoo.languages[self.languages[0]]
      # use a blank part2
      part2 = oo.ooline()
    else:
      if self.languages is None:
        part1 = theoo.lines[0]
        part2 = theoo.lines[1]
      else:
        part1 = theoo.languages[self.languages[0]]
        part2 = theoo.languages[self.languages[1]]
    key = self.makekey(part1.getkey())
    textpo = self.makepo(part1, part2, key, 'text')
    quickhelppo = self.makepo(part1, part2, key, 'quickhelptext')
    titlepo = self.makepo(part1, part2, key, 'title')
    polist = [textpo, quickhelppo, titlepo]
    return polist

  def convertfile(self, theoofile, filename="unknown file"):
    """converts an entire oo file to .po format"""
    thepofile = po.pofile()
    # create a header for the file
    headerpo = po.poelement()
    headerpo.othercomments.append("# extracted from %s\n" % filename)
    headerpo.msgid = ['""']
    headeritems = [""]
# SOME DESCRIPTIVE TITLE.
# Copyright (C) YEAR Free Software Foundation, Inc.
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
#
#, fuzzy
    headeritems.append("Project-Id-Version: PACKAGE VERSION\\n")
    headeritems.append("POT-Creation-Date: 2002-07-15 17:13+0100\\n")
    headeritems.append("PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n")
    headeritems.append("Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n")
    headeritems.append("Language-Team: LANGUAGE <LL@li.org>\\n")
    headeritems.append("MIME-Version: 1.0\\n")
    headeritems.append("Content-Type: text/plain; charset=ISO-8859-1\\n")
    headeritems.append("Content-Transfer-Encoding: ENCODING\\n")
    headerpo.msgstr = [quote.quotestr(str) for str in headeritems]
    thepofile.poelements.append(headerpo)
    # go through the oo and convert each element
    for theoo in theoofile.ooelements:
      polist = self.convertelement(theoo)
      for thepo in polist:
        # print >>sys.stderr, "%r" % thepo.msgid
        thepofile.poelements.append(thepo)
    thepofile.removeblanks()
    return thepofile

def convertfile(inputfile, outputfile, blankmsgstr):
  """reads in stdin using fromfileclass, converts using convertorclass, writes to stdout"""
  fromfile = oo.oofile()
  filelines = inputfile.readlines()
  fromfile.fromlines(filelines)
  convertor = oo2po(blankmsgstr=blankmsgstr)
  outputpo = convertor.convertfile(fromfile)
  outputpolines = outputpo.tolines()
  outputfile.writelines(outputpolines)

def recurse(inputdir, outputdir, inputformat, outputformat, blankmsgstr):
  dirstack = ['']
  while dirstack:
    top = dirstack.pop(-1)
    names = os.listdir(os.path.join(inputdir, top))
    dirs = []
    for name in names:
      inputname = os.path.join(inputdir, top, name)
      # handle directories...
      if os.path.isdir(inputname):
        dirs.append(os.path.join(top, name))
        outputname = os.path.join(outputdir, top, name)
        if not os.path.isdir(outputname):
          os.mkdir(outputname)
      elif os.path.isfile(inputname):
        # only handle names that match the correct extension...
        base, inputext = os.path.splitext(name)
        if inputext != os.extsep + inputformat:
          print >>sys.stderr, "not processing %s: wrong extension (%r != %r)" % (name, inputext, inputformat)
          continue
        outputname = os.path.join(outputdir, top, base) + os.extsep + outputformat
        inputfile = open(inputname, 'r')
        outputfile = open(outputname, 'w')
        convertfile(inputfile, outputfile, blankmsgstr)
    # make sure the directories are processed next time round...
    dirs.reverse()
    dirstack.extend(dirs)

def handleoptions(options, inputformat, outputformat):
  """handles the options, allocates files, and runs the neccessary functions..."""
  if options.recursive:
    if options.pot:
      outputformat = "pot"
    if options.inputfile is None:
      raise optparse.OptionValueError("cannot use stdin for recursive run. please specify inputfile")
    if not os.path.isdir(options.inputfile):
      raise optparse.OptionValueError("inputfile must be directory for recursive run.")
    if options.outputfile is None:
      raise optparse.OptionValueError("must specify output directory for recursive run.")
    if not os.path.isdir(options.outputfile):
      raise optparse.OptionValueError("output must be existing directory for recursive run.")
    recurse(options.inputfile, options.outputfile, inputformat, outputformat, options.pot)
  else:
    if options.inputfile is None:
      inputfile = sys.stdin
    else:
      inputfile = open(options.inputfile, 'r')
    if options.outputfile is None:
      outputfile = sys.stdout
    else:
      outputfile = open(options.outputfile, 'w')
    convertfile(inputfile, outputfile, options.pot)

if __name__ == '__main__':
  # handle command line options
  try:
    import optparse
  except ImportError:
    from translate.misc import optparse
  inputformat = "oo"
  outputformat = "po"
  parser = optparse.OptionParser(usage="%prog [options] [-i|--input-file inputfile] [-o|--output-file outputfile]")
  parser.add_option("-R", "--recursive", action="store_true", dest="recursive", default=False, \
                    help="recurse subdirectories")
  parser.add_option("-P", "--pot", action="store_true", dest="pot", default=False, \
                    help="produce PO template (.pot) with blank msgstrs")
  parser.add_option("-i", "--input-file", dest="inputfile", default=None,
                    help="read from inputfile in "+inputformat+" format", metavar="inputfile")
  parser.add_option("-o", "--output-file", dest="outputfile", default=None,
                    help="write to outputfile in "+outputformat+" format", metavar="outputfile")
  (options, args) = parser.parse_args()
  # open the appropriate files
  try:
    handleoptions(options, inputformat, outputformat)
  except optparse.OptParseError, message:
    parser.error(message)

