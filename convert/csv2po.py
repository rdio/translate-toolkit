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

"""simple script to convert a comma-separated values (.csv) file to a gettext .po localization file"""

import sys
from translate.misc import quote
from translate.misc import sparse
from translate.storage import po
from translate.storage import csvl10n

class csv2po:
  def convertstrings(self,thecsv,thepo):
    # currently let's just get the source, msgid and msgstr back
    thepo.sourcecomments = ["#: " + thecsv.source + "\n"]
    thepo.msgid = [quote.quotestr(line) for line in thecsv.msgid.split('\n')]
    thepo.msgstr = [quote.quotestr(line) for line in thecsv.msgstr.split('\n')]

  def convertelement(self,thecsv):
     thepo = po.poelement()
     self.convertstrings(thecsv,thepo)
     return thepo

  def convertfile(self, thecsvfile):
    thepofile = po.pofile()
    for thecsv in thecsvfile.csvelements:
      thepo = self.convertelement(thecsv)
      if thepo is not None:
        thepofile.poelements.append(thepo)
    return thepofile

def simplify(string):
  return filter(str.isalnum, string)
  tokens = sparse.tokenize(string)
  return " ".join(tokens)

def replacestrings(source, *pairs):
  for orig, new in pairs:
    source = source.replace(orig, new)
  return source

def quotecsvstr(source):
  return '"' + replacestrings(source, ('\\"','"'), ('"','\\"'), ("\\\\'", "\\'"), ('\\\\n', '\\n')) + '"'

class repo:
  """a class that takes translations from a .csv file and puts them in a .po file"""
  def __init__(self, templatepo):
    """construct the converter..."""
    self.unmatched = 0
    self.p = templatepo
    self.makeindex()

  def makeindex(self):
    """makes indexes required for searching..."""
    self.sourceindex = {}
    self.msgidindex = {}
    self.simpleindex = {}
    for thepo in self.p.poelements:
      sourceparts = []
      for sourcecomment in thepo.sourcecomments:
        sourceparts.append(sourcecomment.replace("#:","",1).strip())
      source = " ".join(sourceparts)
      unquotedid = po.getunquotedstr(thepo.msgid)
      # the definitive way to match is by source
      self.sourceindex[source] = thepo
      # do simpler matching in case things have been mangled...
      simpleid = simplify(unquotedid)
      # but check for duplicates
      if simpleid in self.simpleindex and not (unquotedid in self.msgidindex):
        # keep a list of them...
        self.simpleindex[simpleid].append(thepo)
      else:
        self.simpleindex[simpleid] = [thepo]
      # also match by standard msgid
      self.msgidindex[unquotedid] = thepo

  def handlecsvelement(self, thecsv):
    """handles reintegrating a csv element into the .po file"""
    if len(thecsv.source.strip()) == 0 and thecsv.msgid.find("Content-Type:") != -1:
      # this is the header string, we don't need to do anything with it
      return
    if len(thecsv.source.strip()) > 0 and thecsv.source in self.sourceindex:
      thepo = self.sourceindex[thecsv.source]
    elif thecsv.msgid in self.msgidindex:
      thepo = self.msgidindex[thecsv.msgid]
    elif simplify(thecsv.msgid) in self.simpleindex:
      thepolist = self.simpleindex[simplify(thecsv.msgid)]
      if len(thepolist) > 1:
        print >>sys.stderr, "trying to match by duplicate simpleid: original %s, simplified %s" % (thecsv.msgid, simplify(thecsv.msgid))
        print >>sys.stderr, "\n".join(["possible match: " + po.getunquotedstr(thepo.msgid) for thepo in thepolist])
        self.unmatched += 1
        return
      thepo = thepolist[0]
    else:
      print >>sys.stderr, "could not find csv entry in po: %r, %r, %r" % (thecsv.source, thecsv.msgid, thecsv.msgstr)
      self.unmatched += 1
      return
    thepo.msgstr = [quotecsvstr(quote.doencode(line)) for line in thecsv.msgstr.split('\n')]

  def convertfile(self, csvfile):
    """takes the translations from the given csvfile and puts them into the pofile"""
    self.c = csvfile
    # translate the strings
    for thecsv in self.c.csvelements:
      # there may be more than one element due to msguniq merge
      self.handlecsvelement(thecsv)
    print >>sys.stderr, "%d unmatched out of %d strings" % (self.unmatched, len(self.p.poelements))
    missing = 0
    for thepo in self.p.poelements:
      if len(po.getunquotedstr(thepo.msgstr).strip()) == 0:
        missing += 1
    print >>sys.stderr, "%d still missing out of %d strings" % (missing, len(self.p.poelements))
    # returned the transformed po
    return self.p

def convertcsv(inputfile, outputfile, templatefile):
  """reads in inputfile using csvl10n, converts using csv2po, writes to outputfile"""
  inputcsv = csvl10n.csvfile(inputfile)
  if templatefile is None:
    convertor = csv2po()
  else:
    templatepo = po.pofile(templatefile)
    convertor = repo(templatepo)
  outputpo = convertor.convertfile(inputcsv)
  if outputpo.isempty():
    return 0
  outputpolines = outputpo.tolines()
  outputfile.writelines(outputpolines)
  return 1

if __name__ == '__main__':
 # handle command line options
  from translate.convert import convert
  inputformats = {"csv": convertcsv}
  outputformat = "po"
  parser = convert.ConvertOptionParser(convert.optionalrecursion, inputformats, outputformat, usetemplates=True, templateslikeinput=False)
  (options, args) = parser.parse_args()
  try:
    parser.runconversion(options, None)
  except convert.optparse.OptParseError, message:
    parser.error(message)

