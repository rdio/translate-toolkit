#!/usr/bin/python2.2
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
gettext-style .po (or .pot) files are used in translations for KDE et al (see kbabel)
FIXME: add simple test which reads in a file and writes it out again"""

from __future__ import generators
from translate.misc import quote

def getunquotedstr(lines):
  esc = '\\'
  thestr = "\n".join([quote.extractwithoutquotes(line,'"','"',esc,includeescapes=0)[0] for line in lines])
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
    self.msgstr = []

  def merge(self, otherpo):
    """merges the otherpo (with the same msgid) into this one"""
    self.othercomments.extend(otherpo.othercomments)
    self.sourcecomments.extend(otherpo.sourcecomments)
    self.typecomments.extend(otherpo.typecomments)
    self.visiblecomments.extend(otherpo.visiblecomments)
    self.msgidcomments.extend(otherpo.msgidcomments)
    if len("".join(self.msgstr).strip()) == 0:
      self.msgstr = otherpo.msgstr
    elif len("".join(otherpo.msgstr).strip()) <> 0:
      if self.msgstr != otherpo.msgstr:
        if not self.isfuzzy():
          self.typecomments.append("#, fuzzy\n")

  def isheader(self):
    msgidlen = len(getunquotedstr(self.msgid).strip())
    msgstrlen = len(getunquotedstr(self.msgstr).strip())
    return (msgidlen == 0) and (msgstrlen > 0)

  def isblank(self):
    if self.isheader():
      return 0
    if (len("".join(self.msgid).strip()) == 0) and (len("".join(self.msgstr).strip()) == 0):
      return 1
    unquotedid = [quote.extractwithoutquotes(line,'"','"','\\',includeescapes=0)[0] for line in self.msgid]
    if len("".join(unquotedid).strip()) == 0:
      return 1

  def hastypecomment(self, typecomment):
    return ("".join(self.typecomments)).find(typecomment) != -1

  def isfuzzy(self):
    return self.hastypecomment("fuzzy")

  def isnotblank(self):
    return not self.isblank()

  def fromlines(self,lines):
    inmsgid = 0
    inmsgstr = 0
    linesprocessed = 0
    for line in lines:
      linesprocessed += 1
      if line[0] == '#':
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
        if line[:5] == 'msgid':
          inmsgid = 1
          inmsgstr = 0
        elif line[:6] == 'msgstr':
          inmsgstr = 1
          inmsgid = 0
      str = quote.extractstr(line)
      if not str is None:
        if inmsgid:
          # self.othercomments.append("# msgid=["+repr(str)+","+repr(str[:2])+"]\n")
          if str.find('_:') != -1:
            self.msgidcomments.append(str)
          else:
            self.msgid.append(str)
        elif inmsgstr:
          self.msgstr.append(str)
    return linesprocessed

  def tolines(self):
    for othercomment in self.othercomments:
      yield othercomment
    for sourcecomment in self.sourcecomments:
      yield sourcecomment
    for typecomment in self.typecomments:
      yield typecomment
    for visiblecomment in self.visiblecomments:
      yield visiblecomment
    # if there's no msgid don't do msgid and string, unless we're the header
    if (len(self.msgid) == 0) or ((len(self.msgid) == 1) and (self.msgid[0] == '""')):
      if not self.isheader():
        return
    msgidstr = "msgid "
    msgidstartline = 0
    if len(self.msgid) > 0 and len(self.msgidcomments) == 0:
      msgidstr += self.msgid[0]
      msgidstartline = 1
    elif len(self.msgidcomments) > 0:
      if len(self.msgid) > 0 and len(getunquotedstr([self.msgid[0]])) == 0:
        # if there is a blank leader line, it must come before the comment
        msgidstr += self.msgid[0] + '\n'
        msgidstartline += 1
      # comments first, no blank leader line needed
      for msgidcomment in self.msgidcomments:
        msgidstr += msgidcomment # + '\n'
      msgidstr = quote.rstripeol(msgidstr)
    else:
      msgidstr += '""'
    yield msgidstr + '\n'
    # add the rest
    for msgidline in self.msgid[msgidstartline:]:
      yield msgidline + '\n'
    msgstrstr = "msgstr "
    if len(self.msgstr) > 0:
      msgstrstr += self.msgstr[0]
    else:
      msgstrstr = '""'
    yield msgstrstr + '\n'
    # add the rest
    for msgstrline in self.msgstr[1:]:
      yield msgstrline + '\n'

  def getsources(self):
    """returns the list of sources from sourcecomments in the po element"""
    sources = []
    for sourcecomment in self.sourcecomments:
      sources += quote.rstripeol(sourcecomment)[3:].split()
    return sources

class pofile:
  def __init__(self, inputfile=None):
    self.poelements = []
    self.filename = getattr(inputfile, 'name', '')
    if inputfile is not None:
      polines = inputfile.readlines()
      inputfile.close()
      self.fromlines(polines)

  def fromlines(self,lines):
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
      if msgid in msgiddict:
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
      sources = thepo.getsources()
      if len(sources) == 0:
        msgid = getunquotedstr(thepo.msgid)
        self.msgidindex[msgid] = thepo
      for source in thepo.getsources():
        if source in self.sourceindex:
          # if sources aren't unique, don't use them
          if self.sourceindex[source] is not None:
            previouspo = self.sourceindex[source]
            previousmsgid = getunquotedstr(previouspo.msgid)
            self.msgidindex[previousmsgid] = previouspo
            self.sourceindex[source] = None
          msgid = getunquotedstr(thepo.msgid)
          self.msgidindex[msgid] = thepo
        else:
          self.sourceindex[source] = thepo

  def tolines(self):
    lines = []
    for pe in self.poelements:
      pelines = pe.tolines()
      lines.extend(pelines)
      # add a line break
      lines.append('\n')
    return lines

  def todict(self):
    """returns a dictionary of elements based on msgid"""
    return dict([(" ".join(poel.msgid), poel) for poel in self.poelements])

if __name__ == '__main__':
  import sys
  pf = pofile(sys.stdin)
  sys.stdout.writelines(pf.tolines())

