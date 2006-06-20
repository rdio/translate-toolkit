#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2006 Zuza Software Foundation
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

"""Converts plain text files to Gettext .po files
You can convert back to .txt using po2txt"""

from translate.storage import po
from translate.misc import quote

class txt2po:
  def convertblock(self, filename, block, linenum):
    """makes a pounit based on the current block"""
    thepo = po.pounit(encoding="UTF-8")
    thepo.sourcecomments.append("#: %s:%d\n" % (filename,linenum+1))
    thepo.msgid = [quote.quotestr(quote.rstripeol(line)) for line in block]
    if len(thepo.msgid) > 1:
      thepo.msgid = [quote.quotestr("")] + thepo.msgid
    thepo.msgstr = []
    return thepo

  def convertfile(self, inputfile, filename, includeheader):
    """converts a file to .po format"""
    thepofile = po.pofile()
    if includeheader:
      headerpo = thepofile.makeheader(charset="UTF-8", encoding="8bit")
      thepofile.units.append(headerpo)
    lines = inputfile.readlines()
    block = []
    startline = 0
    for linenum in range(len(lines)):
      line = lines[linenum]
      isbreak = not line.strip()
      if isbreak and block:
        thepo = self.convertblock(filename, block, startline)
        thepofile.units.append(thepo)
        block = []
      elif not isbreak:
        if not block:
          startline = linenum
        block.append(line)
    if block:
      thepo = self.convertblock(filename, block, startline)
      thepofile.units.append(thepo)
    return thepofile

def converttxt(inputfile, outputfile, templates):
  """reads in stdin using fromfileclass, converts using convertorclass, writes to stdout"""
  convertor = txt2po()
  outputfilepos = outputfile.tell()
  includeheader = outputfilepos == 0
  outputpo = convertor.convertfile(inputfile, getattr(inputfile, "name", "unknown"), includeheader)
  outputposrc = str(outputpo)
  outputfile.write(outputposrc)
  return 1

def main(argv=None):
  from translate.convert import convert
  formats = {"txt":("po",converttxt), "*":("po",converttxt)}
  parser = convert.ConvertOptionParser(formats, usepots=True, description=__doc__)
  parser.run(argv)

