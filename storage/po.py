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

"""classes that hold elements of .po files (poelement) or entire files (pofile)
gettext-style .po (or .pot) files are used in translations for KDE et al (see kbabel)"""

from __future__ import generators
from translate.misc import quote

def getunquotedstr(lines):
  esc = '\\'
  thestr = "\n".join([quote.extractwithoutquotes(line,'"','"',esc,includeescapes=1)[0] for line in lines])
  if thestr[:1] == "\n": thestr = thestr[1:]
  if thestr[-1:] == "\n": thestr = thestr[:-1]
  return thestr

"""
From the GNU gettext manual:
     WHITE-SPACE
     #  TRANSLATOR-COMMENTS
     #. AUTOMATIC-COMMENTS
     #: REFERENCE...
     #, FLAG...
     msgid UNTRANSLATED-STRING
     msgstr TRANSLATED-STRING
"""

class poelement:
  # othercomments = []      #   # this is another comment
  # sourcecomments = []     #   #: sourcefile.xxx:35
  # typecomments = []       #   #, fuzzy
  # visiblecomments = []    #   #_ note to translator  (this is nonsense)
  # msgid = []
  # msgstr = []

  def __init__(self):
    self.othercomments = []
    self.sourcecomments = []
    self.typecomments = []
    self.visiblecomments = []
    self.msgidcomments = []
    self.msgid = []
    self.msgid_pluralcomments = []
    self.msgid_plural = []
    self.msgstr = []

  def msgidlen(self):
    return len(getunquotedstr(self.msgid).strip())

  def msgstrlen(self):
    if isinstance(self.msgstr, dict):
      return len(getunquotedstr("\n".join(self.msgstr)).strip())
    else:
      return len(getunquotedstr(self.msgstr).strip())

  def merge(self, otherpo):
    """merges the otherpo (with the same msgid) into this one"""
    self.othercomments.extend(otherpo.othercomments)
    self.sourcecomments.extend(otherpo.sourcecomments)
    self.typecomments.extend(otherpo.typecomments)
    self.visiblecomments.extend(otherpo.visiblecomments)
    self.msgidcomments.extend(otherpo.msgidcomments)
    if self.isblankmsgstr():
      self.msgstr = otherpo.msgstr
    elif not other.isblankmsgstr():
      if self.msgstr != otherpo.msgstr:
        if not self.isfuzzy():
          self.typecomments.append("#, fuzzy\n")

  def isheader(self):
    return (self.msgidlen() == 0) and (self.msgstrlen() > 0)

  def isblank(self):
    if self.isheader():
      return False
    if (self.msgidlen() == 0) and (self.msgstrlen() == 0):
      return True
    unquotedid = [quote.extractwithoutquotes(line,'"','"','\\',includeescapes=0)[0] for line in self.msgid]
    return len("".join(unquotedid).strip()) == 0

  def isblankmsgstr(self):
    """checks whether the msgstr is blank"""
    return self.msgstrlen() == 0

  def hastypecomment(self, typecomment):
    return ("".join(self.typecomments)).find(typecomment) != -1

  def isfuzzy(self):
    return self.hastypecomment("fuzzy")

  def isnotblank(self):
    return not self.isblank()

  def hasplural(self):
    """returns whether this poelement contains plural strings..."""
    return len(self.msgid_plural) > 0

  def fromlines(self,lines):
    inmsgid = 0
    inmsgid_plural = 0
    inmsgstr = 0
    msgstr_pluralid = None
    linesprocessed = 0
    for line in lines:
      linesprocessed += 1
      if len(line) == 0:
        continue
      elif line[0] == '#':
        if inmsgstr:
          # if we're already in the message string, this is from the next element
          break
        if line[1] == ':':
          self.sourcecomments.append(line)
        elif line[1] == ',':
          self.typecomments.append(line)
        elif line[1] == '_':
          self.visiblecomments.append(line)
        else:
          self.othercomments.append(line)
      else:
        if line.startswith('msgid_plural'):
          inmsgid = 0
          inmsgid_plural = 1
          inmsgstr = 0
        elif line.startswith('msgid'):
          inmsgid = 1
          inmsgid_plural = 0
          inmsgstr = 0
        elif line.startswith('msgstr'):
          inmsgid = 0
          inmsgid_plural = 0
          inmsgstr = 1
          if line.startswith('msgstr['):
            msgstr_pluralid = int(line[len('msgstr['):line.find(']')].strip())
          else:
            msgstr_pluralid = None
      extracted = quote.extractstr(line)
      if not extracted is None:
        if inmsgid:
          # self.othercomments.append("# msgid=["+repr(extracted)+","+repr(extracted[:2])+"]\n")
          if extracted.find('_:') != -1:
            self.msgidcomments.append(extracted)
          else:
            self.msgid.append(extracted)
        elif inmsgid_plural:
          if extracted.find('_:') != -1:
            self.msgid_pluralcomments.append(extracted)
          else:
            self.msgid_plural.append(extracted)
        elif inmsgstr:
          if msgstr_pluralid is None:
            self.msgstr.append(extracted)
          else:
            if type(self.msgstr) == list:
              self.msgstr = {0: self.msgstr}
            if msgstr_pluralid not in self.msgstr:
              self.msgstr[msgstr_pluralid] = []
            self.msgstr[msgstr_pluralid].append(extracted)
    return linesprocessed

  def getmsgpartstr(self, partname, partlines, partcomments=""):
    if isinstance(partlines, dict):
      partkeys = partlines.keys()
      partkeys.sort()
      return "".join([self.getmsgpartstr("%s[%d]" % (partname, partkey), partlines[partkey], partcomments) for partkey in partkeys])
    partstr = partname + " "
    partstartline = 0
    if len(partlines) > 0 and len(partcomments) == 0:
      partstr += partlines[0]
      partstartline = 1
    elif len(partcomments) > 0:
      if len(partlines) > 0 and len(getunquotedstr(partlines[:1])) == 0:
        # if there is a blank leader line, it must come before the comment
        partstr += partlines[0] + '\n'
        partstartline += 1
      # comments first, no blank leader line needed
      for partcomment in partcomment:
        partstr += partcomment # + '\n'
      partstr = quote.rstripeol(partstr)
    else:
      partstr += '""'
    partstr += '\n'
    # add the rest
    for partline in partlines[partstartline:]:
      partstr += partline + '\n'
    return partstr

  def tolines(self):
    for othercomment in self.othercomments:
      yield othercomment
    # if there's no msgid don't do msgid and string, unless we're the header
    # this will also discard any comments other than plain othercomments...
    if (len(self.msgid) == 0) or ((len(self.msgid) == 1) and (self.msgid[0] == '""')):
      if not self.isheader():
        return
    for sourcecomment in self.sourcecomments:
      yield sourcecomment
    for typecomment in self.typecomments:
      yield typecomment
    for visiblecomment in self.visiblecomments:
      yield visiblecomment
    yield self.getmsgpartstr("msgid", self.msgid, self.msgidcomments)
    if self.msgid_plural or self.msgid_pluralcomments:
      yield self.getmsgpartstr("msgid_plural", self.msgid_plural, self.msgid_pluralcomments)
    yield self.getmsgpartstr("msgstr", self.msgstr)

  def getsources(self):
    """returns the list of sources from sourcecomments in the po element"""
    sources = []
    for sourcecomment in self.sourcecomments:
      sources += quote.rstripeol(sourcecomment)[3:].split()
    return sources

class pofile:
  """this represents a .po file containing various poelements"""
  def __init__(self, inputfile=None):
    """construct a pofile, optionally reading in from inputfile"""
    self.poelements = []
    self.filename = getattr(inputfile, 'name', '')
    if inputfile is not None:
      polines = inputfile.readlines()
      inputfile.close()
      self.fromlines(polines)

  def makeheader(self, charset="CHARSET", encoding="ENCODING"):
    """create a header for the given filename"""
    # TODO: clean this up, make it handle all the properties...
    headerpo = poelement()
    headerpo.typecomments.append("#, fuzzy\n")
    headerpo.msgid = ['""']
    headeritems = [""]
    headeritems.append("Project-Id-Version: PACKAGE VERSION\\n")
    headeritems.append("POT-Creation-Date: 2002-07-15 17:13+0100\\n")
    headeritems.append("PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n")
    headeritems.append("Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n")
    headeritems.append("Language-Team: LANGUAGE <LL@li.org>\\n")
    headeritems.append("MIME-Version: 1.0\\n")
    headeritems.append("Content-Type: text/plain; charset=%s\\n" % charset)
    headeritems.append("Content-Transfer-Encoding: %s\\n" % encoding)
    headerpo.msgstr = [quote.quotestr(headerstr) for headerstr in headeritems]
    return headerpo

  def isempty(self):
    """returns whether the po file doesn't contain any definitions..."""
    if len(self.poelements) == 0:
      return 1
    # first we check the header...
    header = self.poelements[0]
    if not (header.isheader() or header.isblank()):
      return 0
    # if there are any other elements, this is only empty if they are blank
    for thepo in self.poelements[1:]:
      if not thepo.isblank():
        return 0
    return 1

  def fromlines(self, lines):
    """read the lines of a po file in and include them as poelements"""
    start = 0
    end = 0
    # make only the first one the header
    linesprocessed = 0
    while end <= len(lines):
      if (end == len(lines)) or (lines[end] == '\n'):   # end of lines or just a carriage return
        finished = 0
        while not finished:
          newpe = poelement()
          linesprocessed = newpe.fromlines(lines[start:end])
          start += linesprocessed
          if linesprocessed > 1:
            self.poelements.append(newpe)
          else:
            finished = 1
      end = end+1

  def removeblanks(self):
    """remove any poelements which say they are blank"""
    self.poelements = filter(poelement.isnotblank, self.poelements)

  def removeduplicates(self):
    """make sure each msgid is unique ; merge comments etc from duplicates into original"""
    msgiddict = {}
    uniqueelements = []
    # index everything
    for thepo in self.poelements:
      msgid = getunquotedstr(thepo.msgid)
      if not msgid:
        # blank msgids shouldn't be merged...
        uniqueelements.append(thepo)
      elif msgid in msgiddict:
        msgiddict[msgid].merge(thepo)
      else:
        msgiddict[msgid] = thepo
        uniqueelements.append(thepo)
    self.poelements = uniqueelements

  def makeindex(self):
    """creates an index of po elements based on source comments"""
    self.sourceindex = {}
    self.msgidindex = {}
    for thepo in self.poelements:
      msgid = getunquotedstr(thepo.msgid)
      self.msgidindex[msgid] = thepo
      if thepo.hasplural():
        msgid_plural = getunquotedstr(thepo.msgid_plural)
        self.msgidindex[msgid_plural] = thepo
      for source in thepo.getsources():
        if source in self.sourceindex:
          # if sources aren't unique, don't use them
          self.sourceindex[source] = None
        else:
          self.sourceindex[source] = thepo

  def tolines(self):
    """convert the poelements back to lines"""
    lines = []
    for pe in self.poelements:
      pelines = pe.tolines()
      lines.extend(pelines)
      # add a line break
      lines.append('\n')
    return lines

  def todict(self):
    """returns a dictionary of elements based on msgid"""
    # NOTE: these elements are quoted strings
    # TODO: make them unquoted strings, if useful...
    return dict([(" ".join(poel.msgid), poel) for poel in self.poelements])

if __name__ == '__main__':
  import sys
  pf = pofile(sys.stdin)
  sys.stdout.writelines(pf.tolines())

