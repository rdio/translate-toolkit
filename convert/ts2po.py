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

"""Converts Qt .ts localization files to Gettext .po files
You can convert back to .ts using po2ts"""

from translate.storage import po
from translate.storage import ts
from translate.misc import quote

class ts2po:
  def convertmessage(self, contextname, messagenum, msgid, msgstr, msgcomments, msgtype):
    """makes a poelement from the given message"""
    thepo = po.poelement()
    thepo.sourcecomments.append("#: %s#%d\n" % (contextname, messagenum))
    thepo.msgid = [quote.quotestr(quote.rstripeol(line)) for line in msgid.split("\n")]
    if len(thepo.msgid) > 1:
      thepo.msgid = [quote.quotestr("")] + thepo.msgid
    thepo.msgstr = [quote.quotestr(quote.rstripeol(line)) for line in msgstr.split("\n")]
    if len(msgcomments)>0:
      thepo.othercomments.append("# %s\n" %(msgcomments))
    if msgtype == "unfinished":
      thepo.typecomments.append("#, fuzzy\n")
    if msgtype == "obsolete":
      thepo.visiblecomments.append("#_ OBSOLETE\n")
      # using the fact that -- quote -- "(this is nonsense)"
    return thepo

  def convertfile(self, inputfile):
    """converts a .ts file to .po format"""
    tsfile = ts.QtTsParser(inputfile)
    thepofile = po.pofile()
    headerpo = thepofile.makeheader(charset="UTF-8", encoding="8bit")
    thepofile.poelements.append(headerpo)
    for contextname, messages in tsfile.iteritems():
      messagenum = 0
      for message in messages:
        messagenum += 1
        source = tsfile.getmessagesource(message)
        translation = tsfile.getmessagetranslation(message)
        comment = tsfile.getmessagecomment(message)
        type = tsfile.getmessageattributes(message)
        thepo = self.convertmessage(contextname, messagenum, source, translation, comment, type)
        thepofile.poelements.append(thepo)
    return thepofile

def convertts(inputfile, outputfile, templates):
  """reads in stdin using fromfileclass, converts using convertorclass, writes to stdout"""
  convertor = ts2po()
  outputpo = convertor.convertfile(inputfile)
  outputpolines = outputpo.tolines()
  outputfile.writelines(outputpolines)
  return 1

def main():
  from translate.convert import convert
  formats = {"ts":("po",convertts)}
  parser = convert.ConvertOptionParser(formats, usepots=True, description=__doc__)
  parser.run()

