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

"""Converts .xliff localization files to Gettext .po files
You can convert back to .xliff using po2xliff"""

from translate.storage import po
from translate.storage import xliff
from translate.misc import quote

class xliff2po:
  def converttransunit(self, sources, msgid, msgstr):
    """makes a poelement from the given transunit"""
    thepo = po.poelement()
    if sources:
      thepo.sourcecomments.append("#: %s\n" % " ".join(sources))
    msgid = msgid.replace("\n", "\\n\n")
    msgstr = msgstr.replace("\n", "\\n\n")
    thepo.msgid = [quote.quotestr(quote.rstripeol(line)) for line in msgid.split("\n")]
    if len(thepo.msgid) > 1:
      thepo.msgid = [quote.quotestr("")] + thepo.msgid
    thepo.msgstr = [quote.quotestr(quote.rstripeol(line)) for line in msgstr.split("\n")]
    if len(thepo.msgstr) > 1:
      thepo.msgstr = [quote.quotestr("")] + thepo.msgstr
    return thepo

  def getnodetext(self, node):
    """returns the node's text by iterating through the child nodes"""
    return "".join([t.data for t in node.childNodes if t.nodeType == t.TEXT_NODE])

  def getattrtext(self, node, attrname, default=None):
    """returns the text of an attribute"""
    attrnode = node.attributes.get(attrname, None)
    if attrnode is None:
      return default
    return self.getnodetext(attrnode)

  def gettransunitsources(self, transunit):
    """takes a transunit node and finds the location, returning it in po-style list of sources"""
    sources = []
    for contextgroupnode in transunit.getElementsByTagName("context-group"):
      contextname = self.getattrtext(contextgroupnode, "name")
      if contextname == "x-po-reference":
        sourcefile = ""
        linenumber = None
        for contextnode in contextgroupnode.getElementsByTagName("context"):
          contexttype = self.getattrtext(contextnode, "context-type")
          contexttext = self.getnodetext(contextnode)
          if contexttype == "sourcefile":
            sourcefile = contexttext
          elif contexttype == "linenumber":
            linenumber = contexttext
        source = ""
        if sourcefile: source += sourcefile
        if linenumber: source += ":" + linenumber
        if source: sources.append(source)
    return sources

  def convertfile(self, inputfile):
    """converts a .xliff file to .po format"""
    xlifffile = xliff.XliffParser(inputfile)
    thepofile = po.pofile()
    headerpo = thepofile.makeheader(charset="UTF-8", encoding="8bit")
    # thepofile.poelements.append(headerpo)
    for filename, transunits in xlifffile.iteritems():
      for transunit in transunits:
        sources = self.gettransunitsources(transunit)
        source = xlifffile.gettransunitsource(transunit)
        target = xlifffile.gettransunittarget(transunit)
        thepo = self.converttransunit(sources, source, target)
        thepofile.poelements.append(thepo)
    return thepofile

def convertxliff(inputfile, outputfile, templates):
  """reads in stdin using fromfileclass, converts using convertorclass, writes to stdout"""
  convertor = xliff2po()
  outputpo = convertor.convertfile(inputfile)
  outputpolines = outputpo.tolines()
  outputfile.writelines(outputpolines)
  return 1

def main():
  from translate.convert import convert
  formats = {"xliff":("po",convertxliff)}
  parser = convert.ConvertOptionParser(formats, usepots=True, description=__doc__)
  parser.run()

