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

"""Converts Gettext .po files to .xliff localization files
You can convert back from .xliff to .po using po2xliff"""

from translate.storage import po
from translate.storage import xliff
from translate.misc import quote

class po2xliff:
  def convertfile(self, inputfile, templatefile):
    """converts a .po file to .xliff format"""
    if templatefile is None: 
      xlifffile = xliff.XliffParser()
    else:
      xlifffile = xliff.XliffParser(templatefile)
    thepofile = po.pofile(inputfile)
    for thepo in thepofile.poelements:
      filename = thepo.filename
      if thepo.isblank():
        continue
      source = po.getunquotedstr(thepo.msgid, includeescapes=False)
      translation = po.getunquotedstr(thepo.msgstr, includeescapes=False)
      if isinstance(source, str):
        source = source.decode("utf-8")
      if isinstance(translation, str):
        translation = translation.decode("utf-8")
      sources = []
      for sourcelocation in thepo.getsources():
        if ":" in sourcelocation:
          sourcefile, linenumber = sourcelocation.split(":", 1)
        else:
          sourcefile, linenumber = sourcelocation, ""
      xlifffile.addtranslation(filename, sources, source, translation, createifmissing=True)
    return xlifffile.getxml()

def convertpo(inputfile, outputfile, templatefile):
  """reads in stdin using fromfileclass, converts using convertorclass, writes to stdout"""
  convertor = po2xliff()
  outputxliff = convertor.convertfile(inputfile, templatefile)
  outputfile.write(outputxliff)
  return 1

def main():
  from translate.convert import convert
  formats = {"po": ("xliff", convertpo), ("po", "xliff"): ("xliff", convertpo)}
  parser = convert.ConvertOptionParser(formats, usepots=True, usetemplates=True, description=__doc__)
  parser.run()

