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

"""Converts Gettext .po files to a TMX translation memory file"""

from translate.storage import po
from translate.storage import tmx
from translate.misc import quote

class po2tmx:
  def convertfile(self, inputfile):
    """converts a .po file to TMX file"""
    tmxfile = tmx.TmxParser()
    thepofile = po.pofile(inputfile)
    for thepo in thepofile.poelements:
      # TODO ignore if fuzzy option
      if thepo.isheader() or thepo.isblank() or thepo.isblankmsgstr():
        continue
      source = po.getunquotedstr(thepo.msgid, includeescapes=False)
      translation = po.getunquotedstr(thepo.msgstr, includeescapes=False)
      if isinstance(source, str):
        source = source.decode("utf-8")
      if isinstance(translation, str):
        translation = translation.decode("utf-8")
      # TODO place source location in comments
      # TODO how do we determine the dest lang?
      tmxfile.addtranslation(source, "en", translation, "af")
    return tmxfile.getxml()

def convertpo(inputfile, outputfile, templatefile):
  """reads in stdin using fromfileclass, converts using convertorclass, writes to stdout"""
  convertor = po2tmx()
  outputtmx = convertor.convertfile(inputfile)
  outputfile.write(outputtmx)
  return 1

def main():
  from translate.convert import convert
  formats = {"po": ("tmx", convertpo), ("po", "tmx"): ("tmx", convertpo)}
  parser = convert.ConvertOptionParser(formats, usepots=True, usetemplates=False, description=__doc__)
  parser.run()

