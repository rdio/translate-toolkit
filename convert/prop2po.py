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

from __future__ import generators
import sys
from translate.misc import quote

# the rstripeols convert dos <-> unix nicely as well
# output will be appropriate for the platform

eol = "\n"

class prop2po:
  def convertfile(self, inputfile, outputfile):
    self.inmultilinemsgid = 0
    self.outputheader(outputfile)
    for line in inputfile.xreadlines():
      outputlines = self.convertline(line)
      outputfile.writelines(outputlines)

  def outputheader(self, outputfile):
    # TODO: handle this properly in the pofile class
    outputfile.write('''# extracted from unknown file
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
'''+eol)

  def convertline(self, line):
    """converts a line from properties format..."""
    # escape unicode
    line = quote.escapeunicode(line)
    outputlines = []
    # handle multiline msgid if we're in one
    if self.inmultilinemsgid:
      msgid = quote.rstripeol(line).strip()
      # see if there's more
      self.inmultilinemsgid = (msgid[-1:] == '\\')
      # if we're still waiting for more...
      if self.inmultilinemsgid:
        # strip the backslash
        msgid = msgid[:-1]
      outputlines.append(quote.quotestr(msgid, escapeescapes=1)+eol)
      if not self.inmultilinemsgid:
        # we're finished, print the msgstr
        outputlines.append('msgstr ""'+eol+eol)
    # otherwise, this could be a comment
    elif line.strip()[:1] == '#':
      outputlines.append(quote.rstripeol(line)+eol)
    else:
      equalspos = line.find('=')
      # if no equals, just repeat it
      if equalspos == -1:
        outputlines.append(quote.rstripeol(line)+eol)
      # otherwise, this is a definition
      else:
        name = line[:equalspos].strip()
        msgid = quote.rstripeol(line[equalspos+1:]).strip()
        # simply ignore anything with blank msgid
        if len(msgid) > 0:
          outputlines.append("#: "+name+eol)
          # backslash at end means carry string on to next line
          if msgid[-1:] == '\\':
            self.inmultilinemsgid = 1
            outputlines.append('msgid ""'+eol)
            outputlines.append(quote.quotestr(msgid[:-1], escapeescapes=1)+eol) # don't print the backslash
          else:
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


