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
from translate.storage import po
from translate.storage import csvl10n
from translate import __version__

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
     self.convertstrings(thepo,thecsv)
     return thecsv

  def convertfile(self,thepofile):
    thecsvfile = csvl10n.csvfile()
    for thepo in thepofile.poelements:
      thecsv = self.convertelement(thepo)
      if thecsv is not None:
        thecsvfile.csvelements.append(thecsv)
    return thecsvfile

def main(inputfile, outputfile):
  """reads in inputfile using po, converts using po2csv, writes to outputfile"""
  inputpo = po.pofile(inputfile)
  convertor = po2csv()
  outputcsv = convertor.convertfile(inputpo)
  outputcsvlines = outputcsv.tolines()
  outputfile.writelines(outputcsvlines)

if __name__ == '__main__':
  # handle command line options
  try:
    import optparse
  except ImportError:
    from translate.misc import optparse
  inputformat = "po"
  outputformat = "csv"
  parser = optparse.OptionParser(usage="%prog [-i|--input-file inputfile] [-o|--output-file outputfile]",
                                 version="%prog "+__version__.ver)
  parser.add_option("-i", "--input-file", dest="inputfile", default=None,
                    help="read from inputfile in "+inputformat+" format", metavar="inputfile")
  parser.add_option("-o", "--output-file", dest="outputfile", default=None,
                    help="write to outputfile in "+outputformat+" format", metavar="outputfile")
  (options, args) = parser.parse_args()
  # open the appropriate files
  if options.inputfile is None:
    inputfile = sys.stdin
  else:
    inputfile = open(options.inputfile, 'r')
  if options.outputfile is None:
    outputfile = sys.stdout
  else:
    outputfile = open(options.outputfile, 'w')
  main(inputfile, outputfile)

