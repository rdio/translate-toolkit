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

"""classes that hold elements of .oo files (ooelement) or entire files (oofile)
these are specific .oo files for localisation exported by OpenOffice - SDF format
See http://l10n.openoffice.org/L10N_Framework/Intermediate_file_format.html
FIXME: add simple test which reads in a file and writes it out again"""

import os
import sys
from translate.misc import quote
from translate.misc import wStringIO

normalizetable = ""
for i in map(chr, range(256)):
  if i in "/#.0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ":
    normalizetable += i
  else:
    normalizetable += "_"

def normalizefilename(filename):
  """converts any non-alphanumeric (standard roman) characters to _"""
  return filename.translate(normalizetable)

class ooline:
  """this represents one line, one translation in an .oo file"""
  def __init__(self, parts=None):
    """construct an ooline from its parts"""
    if parts is None:
      self.project, self.sourcefile, self.dummy, self.resourcetype, \
        self.groupid, self.localid, self.helpid, self.platform, self.width, \
        self.languageid, self.text, self.helptext, self.quickhelptext, self.title, self.timestamp = [""] * 15
    else:
      self.setparts(parts)

  def setparts(self, parts):
    """create a line from its tab-delimited parts"""
    if len(parts) != 15:
      print >>sys.stderr, "WRONG SIZE: %r" % parts
      newparts = list(parts)
      if len(newparts) < 15:
        newparts = newparts + [""] * (15-len(newparts))
      else:
        newparts = newparts[:15]
      parts = tuple(newparts)
    self.project, self.sourcefile, self.dummy, self.resourcetype, \
      self.groupid, self.localid, self.helpid, self.platform, self.width, \
      self.languageid, self.text, self.helptext, self.quickhelptext, self.title, self.timestamp = parts

  def getparts(self):
    """return a list of parts in this line"""
    return (self.project, self.sourcefile, self.dummy, self.resourcetype,
            self.groupid, self.localid, self.helpid, self.platform, self.width, 
            self.languageid, self.text, self.helptext, self.quickhelptext, self.title, self.timestamp)

  def toline(self):
    """return a line in tab-delimited form"""
    return "\t".join(self.getparts()).replace("\n", "\\n")

  def getkey(self):
    """get the key that identifies the resource"""
    return (self.project, self.sourcefile, self.resourcetype, self.groupid, self.localid, self.platform)

class ooelement:
  """this represents a number of translations of a resource"""
  def __init__(self):
    """construct the ooelement"""
    self.languages = {}
    self.lines = []

  def addline(self, line):
    """add a line to the ooelement"""
    self.languages[line.languageid] = line
    self.lines.append(line)

  def tolines(self):
    """return the lines in tab-delimited form"""
    return "\r\n".join([line.toline() for line in self.lines])

class oofile:
  """this represents an entire .oo file"""
  def __init__(self):
    """constructs the oofile"""
    self.oolines = []
    self.ooelements = []
    self.ookeys = {}
    self.filename = "(unknown file)"

  def addline(self, thisline):
    """adds a parsed line to the file"""
    key = thisline.getkey()
    element = self.ookeys.get(key, None)
    if element is None:
      element = ooelement()
      self.ooelements.append(element)
      self.ookeys[key] = element
    element.addline(thisline)
    self.oolines.append(thisline)
    
  def fromlines(self, lines):
    """parses lines and adds them to the file"""
    for line in lines:
      parts = quote.rstripeol(line).split("\t")
      thisline = ooline(parts)
      self.addline(thisline)

  def tolines(self):
    """converts all the lines back to tab-delimited form"""
    lines = []
    for oe in self.ooelements:
      if len(oe.lines) > 2:
        for line in oe.lines:
          print >>sys.stderr, line.getparts()
      oeline = oe.tolines() + "\r\n"
      lines.append(oeline)
    return lines

class oomultifile:
  """this takes a huge GSI file and represents it as multiple smaller files..."""
  def __init__(self, filename, mode=None):
    """initialises oomultifile from a seekable inputfile or writable outputfile"""
    self.filename = filename
    if mode is None:
      if os.path.exists(filename):
        mode = 'r'
      else:
        mode = 'w'
    self.mode = mode
    self.multifile = open(filename, mode)
    self.subfilelines = {}
    if mode == "r":
      self.createsubfileindex()

  def createsubfileindex(self):
    """reads in all the lines and works out the subfiles"""
    linenum = 0
    for line in self.multifile:
      subfile = self.getsubfile(line)
      if not subfile in self.subfilelines:
        self.subfilelines[subfile] = []
      self.subfilelines[subfile].append(linenum)
      linenum += 1

  def getsubfile(self, line):
    """looks up the subfile name for the line"""
    if line.count("\t") < 2:
      raise ValueError("invalid tab-delimited line: %r" % line)
    lineparts = line.split("\t", 2)
    module, filename = lineparts[0], lineparts[1]
    filename = filename.replace("\\", "/")
    fileparts = [module] + filename.split("/")
    ooname = os.path.join(*fileparts[:-1])
    return ooname + os.extsep + "oo"

  def listsubfiles(self):
    """returns a list of subfiles in the file"""
    return self.subfilelines.keys()

  def __iter__(self):
   """iterates through the subfile names"""
   for subfile in self.listsubfiles():
     yield subfile

  def __contains__(self, pathname):
    """checks if this pathname is a valid subfile"""
    return pathname in self.subfilelines

  def getlines(self, subfile):
    """returns the list of lines matching the subfile"""
    lines = []
    requiredlines = dict.fromkeys(self.subfilelines[subfile])
    linenum = 0
    self.multifile.seek(0)
    for line in self.multifile:
      if linenum in requiredlines:
        lines.append(line)
      linenum += 1
    return lines

  def openinputfile(self, subfile):
    """returns a pseudo-file object for the given subfile"""
    lines = self.getlines(subfile)
    inputfile = wStringIO.StringIO("".join(lines))
    inputfile.filename = subfile
    return inputfile

  def openoutputfile(self, subfile):
    """returns a pseudo-file object for the given subfile"""
    def onclose(contents):
      self.multifile.write(contents)
    outputfile = wStringIO.CatchStringOutput(onclose)
    outputfile.filename = subfile
    return outputfile

  def getoofile(self, subfile):
    """returns an oofile built up from the given subfile's lines"""
    lines = self.getlines(subfile)
    oofilefromlines = oofile()
    oofilefromlines.filename = subfile
    oofilefromlines.fromlines(lines)
    return oofilefromlines

if __name__ == '__main__':
  of = oofile()
  of.fromlines(sys.stdin.readlines())
  sys.stdout.writelines(of.tolines())


