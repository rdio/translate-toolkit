#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

"""extracts localizable strings from HTML files to gettext .po files
You can merge translated strings back using po2html"""

from translate.storage import po
from translate.storage import html
from translate.misc import quote

class html2po:
  def convertfile(self, inputfile, filename, includeheader, includeuntagged=False):
    """converts a file to .po format"""
    thepofile = po.pofile()
    htmlparser = html.POHTMLParser(includeuntaggeddata=includeuntagged)
    if includeheader:
      headerpo = thepofile.makeheader(charset="UTF-8", encoding="8bit")
      thepofile.units.append(headerpo)
    contents = inputfile.read()
    htmlparser.feed(contents)
    for blocknum in range(len(htmlparser.blocks)):
      block = htmlparser.blocks[blocknum].strip()
      if not block: continue
      thepo = po.pounit(encoding="UTF-8")
      thepo.sourcecomments.append("#: %s:%d\n" % (filename,blocknum+1))
      thepo.msgid = [quote.quotestr(quote.rstripeol(block))]
      if len(thepo.msgid) > 1:
        thepo.msgid = [quote.quotestr("")] + thepo.msgid
      thepo.msgstr = []
      thepofile.units.append(thepo)
    return thepofile

def converthtml(inputfile, outputfile, templates, includeuntagged=False):
  """reads in stdin using fromfileclass, converts using convertorclass, writes to stdout"""
  convertor = html2po()
  outputfilepos = outputfile.tell()
  includeheader = outputfilepos == 0
  outputpo = convertor.convertfile(inputfile, getattr(inputfile, "name", "unknown"), includeheader, includeuntagged)
  outputposrc = str(outputpo)
  outputfile.write(outputposrc)
  return 1

def main(argv=None):
  from translate.convert import convert
  formats = {"html":("po",converthtml), "htm":("po",converthtml)}
  parser = convert.ConvertOptionParser(formats, usepots=True, description=__doc__)
  parser.add_option("-u", "--untagged", dest="includeuntagged", default=False, action="store_true",
                    help="include untagged sections")
  parser.passthrough.append("includeuntagged")
  parser.run(argv)

