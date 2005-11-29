#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
from translate.misc import dictutils
from translate import __version__
import sre
import time

# general functions for quoting / unquoting po strings

def getunquotedstr(lines, joinwithlinebreak=True, includeescapes=True):
  # TODO: try refactor this into unquotefrompo
  """unquotes a string from a po file"""
  if joinwithlinebreak:
    joiner = "\n"
  else:
    joiner = ""
  if isinstance(lines, dict):
    # this might happen if people pass in plural msgstrs ...
    pluralids = lines.keys()
    pluralids.sort()
    return joiner.join([getunquotedstr(lines[pluralid], joinwithlinebreak, includeescapes) for pluralid in pluralids])
  esc = '\\'
  extractline = lambda line: quote.extractwithoutquotes(line,'"','"',esc,includeescapes=includeescapes)[0]
  thestr = joiner.join([extractline(line) for line in lines])
  if thestr[:1] == "\n": thestr = thestr[1:]
  if thestr[-1:] == "\n": thestr = thestr[:-1]
  return thestr

def escapeforpo(line):
  """escapes a line for po format. assumes no \n occurs in the line"""
  return line.replace("\\n", "\n").replace('\\', '\\\\').replace("\n", "\\n").replace('"', '\\"')

def quoteforpo(text):
  """quotes the given text for a PO file, returning quoted and escaped lines"""
  return ['"' + escapeforpo(line) + '"' for line in text.split("\n")]

def isnewlineescape(escape):
  return escape == "\\n"

def isnewlineortabescape(escape):
  return escape == "\\n" or escape == "\\t"

def extractpoline(line):
  backslash = '\\'
  extracted = quote.extractwithoutquotes(line,'"','"',backslash,includeescapes=isnewlineortabescape)[0]
  return extracted # .replace('\\"', '"')

def unquotefrompo(postr, joinwithlinebreak=True):
  if joinwithlinebreak:
    joiner = "\n"
    if postr and postr[0] == '""': postr = postr[1:]
  else:
    joiner = ""
  return joiner.join([extractpoline(line) for line in postr])

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
    newpo = self.__class__()
    newpo.othercomments = self.othercomments[:]
    newpo.sourcecomments = self.sourcecomments[:]
    newpo.typecomments = self.typecomments[:]
    newpo.visiblecomments = self.visiblecomments[:]
    if hasattr(self, "obsoletemessages"):
      newpo.obsoletemessages = self.obsoletemessages[:]
    newpo.msgidcomments = self.msgidcomments[:]
    newpo.msgid = self.msgid[:]
    newpo.msgid_pluralcomments = self.msgid_pluralcomments[:]
    newpo.msgid_plural = self.msgid_plural[:]
    if isinstance(self.msgstr, dict):
      newpo.msgstr = self.msgstr.copy()
    else:
      newpo.msgstr = self.msgstr[:]
    return newpo

  def msgidlen(self):
    if self.hasplural():
      return len(getunquotedstr(self.msgid).strip()) + len(getunquotedstr(self.msgid_plural).strip())
    else:
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
      if unicode in [type(item) for item in list2] + [type(item) for item in list1]:
        for position, item in enumerate(list1):
          if isinstance(item, str):
            list1[position] = item.decode("utf-8")
        for position, item in enumerate(list2):
          if isinstance(item, str):
            list2[position] = item.decode("utf-8")
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

  def hasmarkedcomment(self, commentmarker):
    """check whether the given comment marker is present as # (commentmarker) ..."""
    commentmarker = "(%s)" % commentmarker
    for comment in self.othercomments:
      if comment.replace("#", "", 1).strip().startswith(commentmarker):
        return True
    return False

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
    return self.hastypecomment("review") or self.hasmarkedcomment("review") or self.hasmarkedcomment("pofilter")

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
      # combine comments into one if more then one
      if len(partcomments) > 1:
        combinedcomment = []
        for comment in partcomments:
          comment = unquotefrompo([comment])
          if comment.startswith("_:"):
            comment = comment[len("_:"):]
          if comment.endswith("\\n"):
            comment = comment[:-len("\\n")]
          combinedcomment.append(comment.strip())
        partcomments = quoteforpo("_:%s\\n" % "\n".join(combinedcomment))
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
    """return this po element as a set of lines"""
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
  x_generator = "Translate Toolkit %s" % __version__.ver
  header_order = [
    "Project-Id-Version",
    "Report-Msgid-Bugs-To",
    "POT-Creation-Date",
    "PO-Revision-Date",
    "Last-Translator",
    "Language-Team",
    "MIME-Version",
    "Content-Type",
    "Content-Transfer-Encoding",
    "Plural-Forms",
    "X-Generator",
    ]
  def __init__(self, inputfile=None, encoding=None, elementclass=poelement):
    """construct a pofile, optionally reading in from inputfile.
    encoding can be specified but otherwise will be read from the PO header"""
    self.elementclass = elementclass
    self.poelements = []
    self.filename = ''
    self.encoding = encoding
    if inputfile is not None:
      self.parse(inputfile)

  def parse(self, inputfile):
    """parses the given file"""
    self.filename = getattr(inputfile, 'name', '')
    if inputfile is not None:
      polines = inputfile.readlines()
      inputfile.close()
      self.fromlines(polines)

  def makeheader(self, charset="CHARSET", encoding="ENCODING", project_id_version=None, pot_creation_date=None, po_revision_date=None, last_translator=None, language_team=None, mime_version=None, plural_forms=None, report_msgid_bugs_to=None, **kwargs):
    """create a header for the given filename. arguments are specially handled, kwargs added as key: value
    pot_creation_date can be None (current date) or a value (datetime or string)
    po_revision_date can be None (form), False (=pot_creation_date), True (=now), or a value (datetime or string)"""
    headerargs = dictutils.cidict()
    for key, value in kwargs.iteritems():
      key = key.replace("_", "-")
      if key.islower():
        key = key.title()
      headerargs[key] = value
    headerpo = self.elementclass()
    headerpo.markfuzzy()
    headerpo.msgid = ['""']
    headeritems = [""]
    if project_id_version is None:
      project_id_version = "PACKAGE VERSION"
    if pot_creation_date is None or pot_creation_date == True:
      pot_creation_date = time.strftime("%Y-%m-%d %H:%M%z")
    if isinstance(pot_creation_date, time.struct_time):
      pot_creation_date = pot_creation_date.strftime("%Y-%m-%d %H:%M%z")
    if po_revision_date is None:
      po_revision_date = "YEAR-MO-DA HO:MI+ZONE"
    elif po_revision_date == False:
      po_revision_date = pot_creation_date
    elif po_revision_date == True:
      po_revision_date = time.strftime("%Y-%m-%d %H:%M%z")
    if isinstance(po_revision_date, time.struct_time):
      po_revision_date = po_revision_date.strftime("%Y-%m-%d %H:%M%z")
    if last_translator is None:
      last_translator = "FULL NAME <EMAIL@ADDRESS>"
    if language_team is None:
      language_team = "LANGUAGE <LL@li.org>"
    if mime_version is None:
      mime_version = "1.0"
    if plural_forms is None:
      plural_forms = "nplurals=INTEGER; plural=EXPRESSION;"
    if report_msgid_bugs_to is None:
      report_msgid_bugs_to = ""
    defaultargs = {
      "Project-Id-Version":  project_id_version,
      "Report-Msgid-Bugs-To":  report_msgid_bugs_to,
      "POT-Creation-Date":  pot_creation_date,
      "PO-Revision-Date":  po_revision_date,
      "Last-Translator":  last_translator,
      "Language-Team":  language_team,
      "MIME-Version":  mime_version,
      "Content-Type": "text/plain; charset=%s" % charset,
      "Content-Transfer-Encoding":  encoding,
      "Plural-Forms":  plural_forms,
      "X-Generator": self.x_generator,
      }
    for key in self.header_order:
      value = headerargs.pop(key, defaultargs[key])
      headeritems.append("%s: %s\\n" % (key, value))
    for key, value in headerargs.iteritems():
      headeritems.append("%s: %s\\n" % (key, value))
    headerpo.msgstr = [quote.quotestr(headerstr) for headerstr in headeritems]
    return headerpo

  def parseheader(self):
    """parses the values in the header into a dictionary"""
    headervalues = dictutils.ordereddict()
    if len(self.poelements) == 0:
      return headervalues
    header = self.poelements[0]
    if not header.isheader():
      return headervalues
    lineitem = ""
    for line in header.msgstr:
      line = getunquotedstr([line]).strip()
      if line.endswith("\\n"):
        lineitem += line[:-2]
      else:
        lineitem += line
        continue
      if not ":" in lineitem:
        continue
      key, value = lineitem.split(":", 1)
      headervalues[key.strip()] = value.strip()
      lineitem = ""
    return headervalues

  def updateheader(self, add=False, **kwargs):
    """update field(s) in the PO header"""
    headeritems = self.parseheader()
    if not headeritems and not add:
      return
    header = self.poelements[0]
    if not header.isheader():
      header = self.makeheader(**kwargs)
      self.poelements.insert(0, header)
      headeritems = self.parseheader()
    else:
      headerargs = dictutils.ordereddict()
      fixedargs = dictutils.cidict()
      for key, value in kwargs.items():
        key = key.replace("_", "-")
        if key.islower():
          key = key.title()
        fixedargs[key] = value
      for key in self.header_order:
        if key in fixedargs:
          headerargs[key] = fixedargs.pop(key)
      for key in fixedargs:
        headerargs[key] = kwargs[key]
      for key, value in headerargs.iteritems():
        if headeritems.has_key(key) or add:
          headeritems[key] = value
    headerlines = [""]
    for key, value in headeritems.items():
      headerlines.append("%s: %s\\n" % (key, value))
    header.msgstr = [quote.quotestr(headerline) for headerline in headerlines]
    header.markfuzzy(False)
    return header

  def updateheaderplural(self, nplurals, plural):
    """update the Plural-Form PO header"""
    if isinstance(nplurals, basestring):
      nplurals = int(nplurals)
    self.updateheader( Plural_Forms = "nplurals=%d; plural=%s;" % (nplurals, plural) )

  def getheaderplural(self):
    """returns the nplural and plural values from the header"""
    pluralformvalue = self.parseheader().get('Plural-Forms', None)
    if pluralformvalue is None:
      return None, None
    nplural = sre.findall("nplurals=(.+?);", pluralformvalue)
    plural = sre.findall("plural=(.+?);", pluralformvalue)
    if nplural[0] == "INTEGER":
      nplural = None
    else:
      nplural = nplural[0]
    if plural[0] == "EXPRESSION":
      plural = None
    else:
      plural = plural[0]
    return nplural, plural

  def changeencoding(self, newencoding):
    """changes the encoding on the file"""
    self.encoding = newencoding
    if not self.poelements:
      return
    header = self.poelements[0]
    if not (header.isheader() or header.isblank()):
      return
    charsetline = None
    headerstr = unquotefrompo(header.msgstr, True)
    for line in headerstr.split("\\n"):
      if not ":" in line: continue
      key, value = line.strip().split(":", 1)
      if key.strip() != "Content-Type": continue
      charsetline = line
    if charsetline is None:
      headerstr += "Content-Type: text/plain; charset=%s" % self.encoding
    else:
      charset = sre.search("charset=([^ ]*)", charsetline)
      if charset is None:
        newcharsetline = charsetline
        if not newcharsetline.strip().endswith(";"):
          newcharsetline += ";"
        newcharsetline += " charset=%s" % self.encoding
      else:
        charset = charset.group(1)
        newcharsetline = charsetline.replace("charset=%s" % charset, "charset=%s" % self.encoding, 1)
      headerstr = headerstr.replace(charsetline, newcharsetline, 1)
    header.msgstr = quoteforpo(headerstr)

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
      if (end == len(lines)) or (not lines[end].strip()):   # end of lines or blank line
        finished = 0
        while not finished:
          newpe = self.elementclass()
          linesprocessed = newpe.fromlines(lines[start:end])
          start += linesprocessed
          if linesprocessed > 1:
            self.poelements.append(newpe)
            if self.encoding is None and newpe.isheader():
              headervalues = self.parseheader()
              contenttype = headervalues.get("Content-Type", None)
              if contenttype is not None:
                charsetmatch = sre.search("charset=([^ ]*)", contenttype)
                self.encoding = charsetmatch and charsetmatch.group(1)
                # now that we know the encoding, decode the whole file
                if self.encoding is not None and self.encoding.lower() != 'charset':
                  lines = self.decode(lines)
          else:
            finished = 1
      end = end+1

  def removeblanks(self):
    """remove any poelements which say they are blank"""
    self.poelements = filter(self.elementclass.isnotblank, self.poelements)

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
    return self.encode(lines)

  def encode(self, lines):
    """encode any unicode strings in lines in self.encoding"""
    newlines = []
    encoding = self.encoding
    if encoding is None or encoding.lower() == "charset":
      encoding = 'UTF-8'
    for line in lines:
      if isinstance(line, unicode):
        line = line.encode(encoding)
      newlines.append(line)
    return newlines

  def decode(self, lines):
    """decode any non-unicode strings in lines with self.encoding"""
    newlines = []
    for line in lines:
      if isinstance(line, str) and self.encoding is not None and self.encoding.lower() != "charset":
        try:
          line = line.decode(self.encoding)
        except UnicodeError, e:
          raise UnicodeError("Error decoding line with encoding %r: %s. Line is %r" % (self.encoding, e, line))
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

