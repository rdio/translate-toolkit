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
  def convertfile(self, inputfile, outputfile):
    self.inmultilinemsgid = 0
    prf = properties.propfile(inputfile)
    alloutputlines = [self.getheader()]
    for pre in prf.propelements:
      outputlines = self.convertelement(pre)
      alloutputlines.extend(outputlines)
    # this code generates munged lines, so we reconstruct them here...
    redolines = [line+'\n' for line in "".join(alloutputlines).split('\n')]
    # this is all so we can remove duplicates.
    # when the po class is used instead of line-by-line processing, this will be easier
    p = po.pofile()
    p.fromlines(redolines)
    p.removeduplicates()
    alloutputlines = p.tolines()
    outputfile.writelines(alloutputlines)

  def getheader(self):
    # TODO: handle this properly in the pofile class
    return '''# extracted from unknown file
#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\\n"
"POT-Creation-Date: 2002-07-15 17:13+0100\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=CHARSET\\n"
"Content-Transfer-Encoding: ENCODING\\n"
'''+eol

  def convertelement(self, pre):
    """converts a properties element from properties format to .po format..."""
    # TODO: make this use the po classes
    # escape unicode
    msgid = quote.escapeunicode(pre.msgid)
    outputlines = pre.comments
    # TODO: handle multiline msgid if we're in one
    if len(msgid) > 0:
      outputlines.append("#: "+pre.name+eol)
      outputlines.append("msgid "+quote.quotestr(msgid, escapeescapes=1)+eol)
      outputlines.append('msgstr ""'+eol+eol)
    return outputlines

def main(inputfile, outputfile):
  convertor = prop2po()
  convertor.convertfile(inputfile, outputfile)

if __name__ == '__main__':
  # handle command line options
  try:
    import optparse
  except ImportError:
    from translate.misc import optparse
  inputformat = "properties"
  outputformat = "po"
  parser = optparse.OptionParser(usage="%prog [-i|--input-file inputfile] [-o|--output-file outputfile]")
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


