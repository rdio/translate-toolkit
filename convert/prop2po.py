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
from translate import __version__

eol = "\n"

class prop2po:
  """convert a .properties file to a .po file for handling the translation..."""
  def convertfile(self, thepropfile, ispotfile=False):
    """converts a .properties file to a .po file..."""
    thepofile = po.pofile()
    if ispotfile:
      headerpo = thepofile.makeheader()
    else:
      headerpo = thepofile.makeheader(charset="UTF-8", encoding="8bit")
    headerpo.othercomments.append("# extracted from %s\n" % thepropfile.filename)
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

  def mergefiles(self, origpropfile, translatedpropfile, blankmsgstr=False):
    """converts a .properties file to a .po file..."""
    thepofile = po.pofile()
    if blankmsgstr:
      headerpo = thepofile.makeheader()
    else:
      headerpo = thepofile.makeheader(charset="UTF-8", encoding="8bit")
    headerpo.othercomments.append("# extracted from %s, %s\n" % (origpropfile.filename, translatedpropfile.filename))
    translatedpropfile.makeindex()
    # we try and merge the header po with any comments at the start of the properties file
    appendedheader = 0
    waitingcomments = []
    # loop through the original file, looking at elements one by one
    for origprop in origpropfile.propelements:
      origpo = self.convertelement(origprop)
      if origpo is None:
        waitingcomments.extend(origprop.comments)
      # handle the header case specially...
      if not appendedheader:
        if origprop.isblank():
          origpo = headerpo
        else:
          thepofile.poelements.append(headerpo)
        appendedheader = 1
      # try and find a translation of the same name...
      if origprop.name in translatedpropfile.index:
        translatedprop = translatedpropfile.index[origprop.name]
        translatedpo = self.convertelement(translatedprop)
      else:
        translatedpo = None
      # if we have a valid po element, get the translation and add it...
      if origpo is not None:
        if translatedpo is not None and not blankmsgstr:
          origpo.msgstr = translatedpo.msgid
        origpo.othercomments = waitingcomments + origpo.othercomments
        waitingcomments = []
        thepofile.poelements.append(origpo)
      elif translatedpo is not None:
        print >>sys.stderr, "error converting original properties definition %s" % origprop.name
    thepofile.removeduplicates()
    return thepofile

  def convertelement(self, theprop):
    """converts a .properties element to a .po element..."""
    # escape unicode
    msgid = quote.escapeunicode(theprop.msgid.strip())
    thepo = po.poelement()
    thepo.othercomments.extend(theprop.comments)
    # TODO: handle multiline msgid
    if theprop.isblank():
      return None
    thepo.sourcecomments.append("#: "+theprop.name+eol)
    thepo.msgid = [quote.quotestr(msgid, escapeescapes=1)]
    thepo.msgstr = ['""']
    return thepo

def convertprop(inputfile, outputfile, templatefile, pot=False):
  """reads in inputfile using properties, converts using prop2po, writes to outputfile"""
  inputprop = properties.propfile(inputfile)
  convertor = prop2po()
  if templatefile is None:
    outputpo = convertor.convertfile(inputprop, ispotfile=pot)
  else:
    templateprop = properties.propfile(templatefile)
    outputpo = convertor.mergefiles(templateprop, inputprop, blankmsgstr=pot)
  if outputpo.isempty():
    return 0
  outputpolines = outputpo.tolines()
  outputfile.writelines(outputpolines)
  return 1

if __name__ == '__main__':
  # handle command line options
  from translate.convert import convert
  formats = {"properties": ("po", convertprop), ("properties", "properties"): ("po", convertprop)}
  parser = convert.ConvertOptionParser(formats, usetemplates=True, usepots=True)
  parser.convertparameters.append("pot")
  parser.runconversion()


