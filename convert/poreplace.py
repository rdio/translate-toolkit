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

"""simple script to do replacements on translated strings inside po files"""

# this is used as the basis for other scripts, it currently replaces nothing

from translate.storage import po

class poreplace:
  def convertstring(self, postr):
    """does the conversion required on the given string (nothing in this case)"""
    return postr

  def convertfile(self, thepofile):
    """goes through a po file and converts each element"""
    for thepo in thepofile.poelements:
      thepo.msgstr = [self.convertstring(postr) for postr in thepo.msgstr]
    return thepofile

  def convertpo(self, inputfile, outputfile, templatefile):
    """reads in inputfile using po, converts using poreplace, writes to outputfile"""
    # note that templatefile is not used, but it is required by the converter...
    inputpo = po.pofile(inputfile)
    if inputpo.isempty():
      return 0
    outputpo = self.convertfile(inputpo)
    outputpolines = outputpo.tolines()
    outputfile.writelines(outputpolines)
    return 1

def main(converterclass):
  # handle command line options
  from translate.convert import convert
  replacer = converterclass()
  formats = {"po":("po",replacer.convertpo), "pot":("pot", replacer.convertpo)}
  parser = convert.ConvertOptionParser(formats, usepots=True)
  parser.run()

if __name__ == '__main__':
  main(poreplace)

