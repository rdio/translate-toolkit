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

"""simple script to convert a mozilla .properties localization file to a
gettext .pot format for translation.
does a line-by-line conversion..."""

import sys
from translate.misc import quote
from translate.storage import po
from translate.storage import properties

eol = "\n"

class prop2po:
  """convert a .properties file to a .po file for handling the translation..."""
  def convertfile(self, thepropfile):
    """converts a .properties file to a .po file..."""
    thepofile = po.pofile()
    headerpo = self.makeheader(thepropfile.filename)
    # we try and merge the header po with any comments at the start of the properties file
    appendedheader = 0
    waitingcomments = []
    for theprop in thepropfile.propelements:
      thepo = self.convertelement(theprop)
      if thepo is None:
        waitingcomments.extend(theprop.comments)
      if not appendedheader:
        if theprop.isblank():
          thepo = headerpo
        else:
          thepofile.poelements.append(headerpo)
        appendedheader = 1
      if thepo is not None:
        thepo.othercomments = waitingcomments + thepo.othercomments
        waitingcomments = []
        thepofile.poelements.append(thepo)
    thepofile.removeduplicates()
    return thepofile

  def makeheader(self, filename):
    """create a header for the given filename"""
    # TODO: handle this in the po class
    headerpo = po.poelement()
    headerpo.othercomments.append("# extracted from %s\n" % filename)
    headerpo.typecomments.append("#, fuzzy\n")
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
    headeritems.append("Content-Type: text/plain; charset=CHARSET\\n")
    headeritems.append("Content-Transfer-Encoding: ENCODING\\n")
    headerpo.msgstr = [quote.quotestr(headerstr) for headerstr in headeritems]
    return headerpo

  def convertelement(self, theprop):
    """converts a .properties element to a .po element..."""
    # escape unicode
    msgid = quote.escapeunicode(theprop.msgid.strip())
    thepo = po.poelement()
    thepo.othercomments.extend(theprop.comments)
    # TODO: handle multiline msgid
    if theprop.isblank():
      return None
    thepo.sourcecomments.extend("#: "+theprop.name+eol)
    thepo.msgid = [quote.quotestr(msgid, escapeescapes=1)]
    thepo.msgstr = ['""']
    return thepo

def main(inputfile, outputfile, templatefile):
  """reads in inputfile using properties, converts using prop2po, writes to outputfile"""
  inputprop = properties.propfile(inputfile)
  convertor = prop2po()
  outputpo = convertor.convertfile(inputprop)
  outputpolines = outputpo.tolines()
  outputfile.writelines(outputpolines)
  convertor.convertfile(inputfile, outputfile)

if __name__ == '__main__':
  # handle command line options
  try:
    import optparse
  except ImportError:
    from translate.misc import optparse
  inputformat = "properties"
  outputformat = "po"
  templateformat = "properties"
  parser = optparse.OptionParser(usage="%prog [-i|--input-file inputfile] [-o|--output-file outputfile]")
  parser.add_option("-i", "--input-file", dest="inputfile", default=None,
                    help="read from inputfile in "+inputformat+" format", metavar="inputfile")
  parser.add_option("-o", "--output-file", dest="outputfile", default=None,
                    help="write to outputfile in "+outputformat+" format", metavar="outputfile")
  parser.add_option("-t", "--template", dest="templatefile", default=None,
                    help="read from template in "+templateformat+" format", metavar="template")
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
  if options.templatefile is None:
    templatefile = None
  else:
    templatefile = open(options.templatefile, 'r')
  main(inputfile, outputfile, templatefile)


