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

"""simple script to convert a gettext .po localization file to a comma-separated values (.csv) file"""

import sys
import os
from translate.storage import po
from translate.storage import csvl10n
from translate import __version__
# FIXME: convert to convert
import optparse

class po2csv:
  def convertstrings(self,thepo,thecsv):
    # currently let's just get the source, msgid and msgstr back
    sourceparts = []
    for sourcecomment in thepo.sourcecomments:
      sourceparts.append(sourcecomment.replace("#:","",1).strip())
    source = " ".join(sourceparts)
    unquotedid = po.getunquotedstr(thepo.msgid)
    unquotedstr = po.getunquotedstr(thepo.msgstr)
    if len(unquotedid) >= 1 and unquotedid[:1] in "-+": unquotedid = "\\" + unquotedid
    if len(unquotedstr) >= 1 and unquotedstr[:1] in "-+": unquotedstr = "\\" + unquotedstr
    thecsv.source = source
    thecsv.msgid = unquotedid
    thecsv.msgstr = unquotedstr

  def convertelement(self,thepo):
     thecsv = csvl10n.csvelement()
     if thepo.isheader():
       thecsv.source = "source"
       thecsv.msgid = "original"
       thecsv.msgstr = "translation"
     else:
       self.convertstrings(thepo,thecsv)
     return thecsv

  def convertfile(self,thepofile):
    thecsvfile = csvl10n.csvfile()
    for thepo in thepofile.poelements:
      thecsv = self.convertelement(thepo)
      if thecsv is not None:
        thecsvfile.csvelements.append(thecsv)
    return thecsvfile

def convertfile(inputfile, outputfile):
  """reads in inputfile using po, converts using po2csv, writes to outputfile"""
  inputpo = po.pofile(inputfile)
  convertor = po2csv()
  outputcsv = convertor.convertfile(inputpo)
  outputcsvlines = outputcsv.tolines()
  outputfile.writelines(outputcsvlines)

def recurse(inputdir, outputdir, inputformat, outputformat):
  """recurse through inputdir and convertfiles in inputformat to outputformat in outputdir"""
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
        convertfile(inputfile, outputfile)
    # make sure the directories are processed next time round...
    dirs.reverse()
    dirstack.extend(dirs)

def handleoptions(options, inputformat, outputformat):
  """handles the options, allocates files, and runs the neccessary functions..."""
  if options.recursive:
    if options.pot:
      inputformat = "pot"
    if options.input is None:
      raise optparse.OptionValueError("cannot use stdin for recursive run. please specify inputfile")
    if not os.path.isdir(options.input):
      raise optparse.OptionValueError("inputfile must be directory for recursive run.")
    if options.output is None:
      raise optparse.OptionValueError("must specify output directory for recursive run.")
    if not os.path.isdir(options.output):
      raise optparse.OptionValueError("output must be existing directory for recursive run.")
    recurse(options.input, options.output, inputformat, outputformat)
  else:
    if options.input is None:
      inputfile = sys.stdin
    else:
      inputfile = open(options.input, 'r')
    if options.output is None:
      outputfile = sys.stdout
    else:
      outputfile = open(options.output, 'w')
    convertfile(inputfile, outputfile)

if __name__ == '__main__':
  # handle command line options
  from translate.convert import convert
  inputformat = "po"
  outputformat = "csv"
  parser = convert.ConvertOptionParser(convert.optionalrecursion, inputformat, outputformat)
  parser.add_option("-P", "--pot", action="store_true", dest="pot", default=False, \
                    help="convert PO template (.pot) with blank msgstrs")
  (options, args) = parser.parse_args()
  # open the appropriate files
  try:
    handleoptions(options, inputformat, outputformat)
  except optparse.OptParseError, message:
    parser.error(message)

