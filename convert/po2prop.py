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


"""script that converts a .po file with translations based on a .pot file
generated from a Mozilla localization .properties back to the .properties (but translated)
Uses the original .properties to do the conversion as this makes sure we don't
leave out any unexpected stuff..."""

from translate.misc import quote
from translate.storage import po
from translate import __version__

eol = "\n"

class reprop:
  def __init__(self, templatefile):
    self.templatefile = templatefile
    self.podict = {}

  def convertfile(self, pofile):
    self.inmultilinemsgid = 0
    self.inecho = 0
    self.makepodict(pofile)
    outputlines = []
    for line in self.templatefile.readlines():
      outputstr = self.convertline(line)
      outputlines.append(outputstr)
    return outputlines

  def makepodict(self, pofile):
    # make a dictionary of the translations
    for thepo in pofile.poelements:
      # there may be more than one entity due to msguniq merge
      entities = []
      for sourcecomment in thepo.sourcecomments:
        entities += quote.rstripeol(sourcecomment)[3:].split()
      for entity in entities:
        # currently let's just get the msgstr back
        # this converts the po-style string to a prop-style string
        # i.e. no quotes but backslash at the end of the line continues to the next
        propstring = self.convertstring(thepo.msgstr)
        if len(propstring.strip()) == 0:
          propstring = self.convertstring(thepo.msgid)
        self.podict[entity] = propstring

  def convertstring(self, postring):
    """converts a po-style string to a properties-style string"""
    propstring = "\\n".join([quote.extractwithoutquotes(line,'"','"',"\\",includeescapes=0)[0] for line in postring])
    if propstring[:2] == "\\n": propstring = propstring[2:]
    print repr((postring, propstring))
    return propstring

  def convertline(self, line):
    # handle multiline msgid if we're in one
    if self.inmultilinemsgid:
      msgid = quote.rstripeol(line).strip()
      # see if there's more
      self.inmultilinemsgid = (msgid[-1:] == '\\')
      # if we're echoing...
      if self.inecho:
        return line
    # otherwise, this could be a comment
    elif line.strip()[:1] == '#':
      return quote.rstripeol(line)+eol
    else:
      equalspos = line.find('=')
      # if no equals, just repeat it
      if equalspos == -1:
        return quote.rstripeol(line)+eol
      # otherwise, this is a definition
      else:
        # backslash at end means carry string on to next line
        if quote.rstripeol(line)[-1:] == '\\':
          self.inmultilinemsgid = 1
        # now deal with the current string...
        name = line[:equalspos].strip()
        if self.podict.has_key(name):
          self.inecho = 0
          postr = self.podict[name].decode('utf8')
          return name+"="+quote.mozillapropertiesencode(postr)+eol
        else:
          self.inecho = 1
          return line+eol
    return ""

def convertprop(inputfile, outputfile, templatefile, showchecks=True):
  inputpo = po.pofile(inputfile)
  if templatefile is None:
    raise ValueError("must have template file for properties files")
    # convertor = po2prop()
  else:
    convertor = reprop(templatefile)
  outputproplines = convertor.convertfile(inputpo)
  outputfile.writelines(outputproplines)
  return 1

if __name__ == '__main__':
  # handle command line options
  from translate.convert import convert
  formats = {("po", "properties"): ("properties", convertprop)}
  parser = convert.ConvertOptionParser(formats, usetemplates=True)
  parser.runconversion()

