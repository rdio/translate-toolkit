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
import sre
import datetime

def getunquotedstr(lines, joinwithlinebreak=True, includeescapes=True):
  """unquotes a string from a po file"""
  if isinstance(lines, dict):
    # this might happen if people pass in plural msgstrs ...
    pluralids = lines.keys()
    pluralids.sort()
    return "\n".join([getunquotedstr(lines[pluralid]) for pluralid in pluralids])
  esc = '\\'
  if joinwithlinebreak:
    joiner = "\n"
  else:
    joiner = ""
  extractline = lambda line: quote.extractwithoutquotes(line,'"','"',esc,includeescapes=includeescapes)[0]
  thestr = joiner.join([extractline(line) for line in lines])
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
  # obsoletemessages = []   #   #~ msgid ""
  # msgidcomments = []      #   _: within msgid
  # msgid = []
  # msgstr = []

  def __init__(self):
    self.othercomments = []
    self.sourcecomments = []
    self.typecomments = []
    self.visiblecomments = []
    self.obsoletemessages = []
    self.msgidcomments = []
    self.msgid = []
    self.msgid_pluralcomments = []
    self.msgid_plural = []
    self.msgstr = []

  def copy(self):
    newpo = poelement()
    newpo.othercomments = self.othercomments
    newpo.sourcecomments = self.sourcecomments
    newpo.typecomments = self.typecomments
    newpo.visiblecomments = self.visiblecomments
    newpo.obsoletemessages = self.obsoletemessages = []
    newpo.msgidcomments = self.msgidcomments
    newpo.msgid = self.msgid
    newpo.msgid_pluralcomments = self.msgid_pluralcomments
    newpo.msgid_plural = self.msgid_plural
    newpo.msgstr = self.msgstr
    return newpo

  def msgidlen(self):
    return len(getunquotedstr(self.msgid).strip())

  def msgstrlen(self):
    if isinstance(self.msgstr, dict):
      combinedstr = "\n".join([getunquotedstr(msgstr).strip() for msgstr in self.msgstr.itervalues()])
      return len(combinedstr.strip())
    else:
      return len(getunquotedstr(self.msgstr).strip())

  def merge(self, otherpo, overwrite=False, comments=True):
    """merges the otherpo (with the same msgid) into this one
    overwrite non-blank self.msgstr only if overwrite is True
    merge comments only if comments is True"""
    def mergelists(list1, list2):
      list1.extend([item for item in list2 if not item in list1])
    if comments:
      mergelists(self.othercomments, otherpo.othercomments)
      mergelists(self.sourcecomments, otherpo.sourcecomments)
      mergelists(self.typecomments, otherpo.typecomments)
      mergelists(self.visiblecomments, otherpo.visiblecomments)
      mergelists(self.obsoletemessages, otherpo.obsoletemessages)
      mergelists(self.msgidcomments, otherpo.msgidcomments)
    if self.isblankmsgstr() or overwrite:
      self.msgstr = otherpo.msgstr
    elif otherpo.isblankmsgstr():
      if self.msgid != otherpo.msgid:
        self.markfuzzy()
    else:
      if self.msgstr != otherpo.msgstr:
        self.markfuzzy()

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
    """check whether the given type comment is present"""
    # check for word boundaries properly by using a regular expression...
    return sum(map(lambda tcline: len(sre.findall("\\b%s\\b" % typecomment, tcline)), self.typecomments)) != 0

  def settypecomment(self, typecomment, present=True):
    """alters whether a given typecomment is present"""
    if self.hastypecomment(typecomment) != present:
      if present:
        self.typecomments.append("#, %s\n" % typecomment)
      else:
        # this should handle word boundaries properly ...
        typecomments = map(lambda tcline: sre.sub("\\b%s\\b[ \t]*" % typecomment, "", tcline), self.typecomments)
        self.typecomments = filter(lambda tcline: tcline.strip() != "#,", typecomments)

  def isfuzzy(self):
    return self.hastypecomment("fuzzy")

  def markfuzzy(self, present=True):
    self.settypecomment("fuzzy", present)

  def isreview(self):
    return self.hastypecomment("review")

  def isnotblank(self):
    return not self.isblank()

  def isobsolete(self):
    return len(self.obsoletemessages) > 0

  def hasplural(self):
    """returns whether this poelement contains plural strings..."""
    return len(self.msgid_plural) > 0

  def fromlines(self,lines):
    inmsgid = 0
    inmsgid_comment = 0
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
        elif line[1] == '~':
          self.obsoletemessages.append(line)
        else:
          self.othercomments.append(line)
      else:
        if line.startswith('msgid_plural'):
          inmsgid = 0
          inmsgid_plural = 1
          inmsgstr = 0
          inmsgid_comment = 0
        elif line.startswith('msgid'):
          inmsgid = 1
          inmsgid_plural = 0
          inmsgstr = 0
          inmsgid_comment = 0
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
          # TODO: improve kde comment detection
          if extracted.find("_:") != -1:
            inmsgid_comment = 1
          if inmsgid_comment:
            self.msgidcomments.append(extracted)
          else:
            self.msgid.append(extracted)
          if inmsgid_comment and extracted.find("\\n") != -1:
            inmsgid_comment = 0
        elif inmsgid_plural:
          if extracted.find("_:") != -1:
            inmsgid_comment = 1
          if inmsgid_comment:
            self.msgid_pluralcomments.append(extracted)
          else:
            self.msgid_plural.append(extracted)
          if inmsgid_comment and extracted.find("\\n") != -1:
            inmsgid_comment = 0
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
        # but if the whole string is blank, leave it in
        if len(partlines) > 1:
          partstartline += 1
      # comments first, no blank leader line needed
      partstr += "\n".join(partcomments)
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
    if self.isobsolete():
      for typecomment in self.typecomments:
        yield typecomment
      for obsoletemessage in self.obsoletemessages:
        yield obsoletemessage
        return
    # if there's no msgid don't do msgid and string, unless we're the header
    # this will also discard any comments other than plain othercomments...
    if (len(self.msgid) == 0) or ((len(self.msgid) == 1) and (self.msgid[0] == '""')):
      if not (self.isheader() or self.msgidcomments):
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
    self.filename = ''
    if inputfile is not None:
      self.parse(inputfile)

  def parse(self, inputfile):
    """parses the given file"""
    self.filename = getattr(inputfile, 'name', '')
    if inputfile is not None:
      polines = inputfile.readlines()
      inputfile.close()
      self.fromlines(polines)

  def makeheader(self, charset="CHARSET", encoding="ENCODING", projectid=None, creationdate=None, revisiondate=None, lasttranslator=None, languageteam=None, mimeversion=None, **kwargs):
    """create a header for the given filename. arguments are specially handled, kwargs added as key: value
    creationdate can be None (current date) or a value (datetime or string)
    revisiondate can be None (form), False (=creationdate), True (=now), or a value (datetime or string)"""
    # TODO: clean this up, make it handle all the properties...
    headerpo = poelement()
    headerpo.markfuzzy()
    headerpo.msgid = ['""']
    headeritems = [""]
    if projectid is None:
      projectid = "PACKAGE VERSION"
    if creationdate is None or creationdate == True:
      creationdate = datetime.datetime.utcnow()
    if not isinstance(creationdate, (str, unicode)):
      creationdate = creationdate.strftime("%F %H:%M%z")
    if revisiondate is None:
      revisiondate = "YEAR-MO-DA HO:MI+ZONE"
    elif revisiondate == False:
      revisiondate = creationdate
    elif revisiondate == True:
      revisiondate = datetime.datetime.utcnow()
    if not isinstance(revisiondate, (str, unicode)):
      revisiondate = revisiondate.strftime("%F %H:%M%z")
    if lasttranslator is None:
      lasttranslator = "FULL NAME <EMAIL@ADDRESS>"
    if languageteam is None:
      languageteam = "LANGUAGE <LL@li.org>"
    if mimeversion is None:
      mimeversion = "1.0"
    addheader = lambda key, value: (key in kwargs) or headeritems.append("%s: %s\\n" % (key, value))
    addheader("Project-Id-Version",  projectid)
    addheader("POT-Creation-Date",  creationdate)
    addheader("PO-Revision-Date",  revisiondate)
    addheader("Last-Translator",  lasttranslator)
    addheader("Language-Team",  languageteam)
    addheader("MIME-Version",  mimeversion)
    addheader("Content-Type", "text/plain; charset=%s" % charset)
    addheader("Content-Transfer-Encoding",  encoding)
    for key, value in kwargs.iteritems():
      headeritems.append("%s: %s\\n" % (key, value))
    headerpo.msgstr = [quote.quotestr(headerstr) for headerstr in headeritems]
    return headerpo

  def parseheader(self):
    """parses the values in the header into a dictionary"""
    headervalues = {}
    if len(self.poelements) == 0:
      return headervalues
    header = self.poelements[0]
    if not header.isheader():
      return headervalues
    lineitem = ""
    for line in header.msgstr:
      line = getunquotedstr([line]).strip()
      if not ":" in line:
        continue
      if line.endswith("\\n"):
        lineitem += line[:-2]
      else:
        lineitem += line
        continue
      key, value = lineitem.split(":", 1)
      headervalues[key.strip()] = value.strip()
      lineitem = ""
    return headervalues

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

  def removeduplicates(self, duplicatestyle="merge"):
    """make sure each msgid is unique ; merge comments etc from duplicates into original"""
    msgiddict = {}
    uniqueelements = []
    # we sometimes need to keep track of what has been marked
    markedpos = {}
    def addcomment(thepo):
      thepo.msgidcomments.append('"_: %s\\n"' % " ".join(thepo.getsources()))
      markedpos[thepo] = True
    for thepo in self.poelements:
      if duplicatestyle.startswith("msgid_comment"):
        msgid = getunquotedstr(thepo.msgidcomments) + getunquotedstr(thepo.msgid)
      else:
        msgid = getunquotedstr(thepo.msgid)
      if not msgid:
        # blank msgids shouldn't be merged...
        uniqueelements.append(thepo)
      elif duplicatestyle == "msgid_comment_all":
        addcomment(thepo)
        uniqueelements.append(thepo)
      elif msgid in msgiddict:
        if duplicatestyle == "merge":
          msgiddict[msgid].merge(thepo)
        elif duplicatestyle == "keep":
          uniqueelements.append(thepo)
        elif duplicatestyle == "msgid_comment":
          origpo = msgiddict[msgid]
          if origpo not in markedpos:
            addcomment(origpo)
          addcomment(thepo)
          uniqueelements.append(thepo)
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
    return self.utf8encode(lines)

  def utf8encode(self, lines):
    """encode any unicode strings in lines as utf8"""
    newlines = []
    for line in lines:
      if isinstance(line, unicode):
        line = line.encode("utf8")
      newlines.append(line)
    return newlines

  def todict(self):
    """returns a dictionary of elements based on msgid"""
    # NOTE: these elements are quoted strings
    # TODO: make them unquoted strings, if useful...
    return dict([(" ".join(poel.msgid), poel) for poel in self.poelements])

if __name__ == '__main__':
  import sys
  pf = pofile(sys.stdin)
  sys.stdout.writelines(pf.tolines())

