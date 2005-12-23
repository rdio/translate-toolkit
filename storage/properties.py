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

"""classes that hold elements of .properties files (propelement) or entire files (propfile)
these files are used in translating Mozilla and other software"""

from translate.misc import quote

# the rstripeols convert dos <-> unix nicely as well
# output will be appropriate for the platform

eol = "\n"

class propelement:
  """an element of a properties file i.e. a name and value, and any comments associated"""
  def __init__(self):
    """construct a blank propelement"""
    self.name = ""
    self.msgid = ""
    self.comments = []

  def isblank(self):
    """returns whether this is a blank element, containing only comments..."""
    return not (self.name or self.msgid)

  def __str__(self):
    """convert the element back into formatted lines for a .properties file"""
    if self.isblank():
      return "".join(self.comments + ["\n"])
    else:
      return "".join(self.comments + ["%s=%s\n" % (self.name, self.msgid)])

class propfile:
  """this class represents a .properties file, made up of propelements"""
  def __init__(self, inputfile=None):
    """construct a propfile, optionally reading in from inputfile"""
    self.propelements = []
    self.filename = getattr(inputfile, 'name', '')
    if inputfile is not None:
      propsrc = inputfile.read()
      inputfile.close()
      self.parse(propsrc)

  def parse(self, propsrc):
    """read the source of a properties file in and include them as propelements"""
    newpe = propelement()
    inmultilinemsgid = 0
    lines = propsrc.split("\n")
    for line in lines:
      # handle multiline msgid if we're in one
      if inmultilinemsgid:
        # handle unicode-escape encoding
        line = quote.mozillapropertiesdecode(line)
        newpe.msgid += quote.rstripeol(line).lstrip()
        # see if there's more
        inmultilinemsgid = (newpe.msgid[-1:] == '\\')
        # if we're still waiting for more...
        if inmultilinemsgid:
          # strip the backslash
          newpe.msgid = newpe.msgid[:-1]
        if not inmultilinemsgid:
          # we're finished, add it to the list...
          self.propelements.append(newpe)
          newpe = propelement()
      # otherwise, this could be a comment
      elif line.strip()[:1] == '#':
        # add a comment
        line = quote.escapecontrols(quote.rstripeol(line))
        newpe.comments.append(line+"\n")
      elif not line.strip():
        # this is a blank line...
        self.propelements.append(newpe)
        newpe = propelement()
      else:
        # handle unicode-escape encoding
        try:
          line = quote.mozillapropertiesdecode(line)
        except UnicodeError, e:
          raise UnicodeError("Error with string %r: %s" % (line, e))
        equalspos = line.find('=')
        # if no equals, just ignore it
        if equalspos == -1:
          continue
        # otherwise, this is a definition
        else:
          newpe.name = line[:equalspos].strip()
          newpe.msgid = quote.rstripeol(line[equalspos+1:]).lstrip()
          # backslash at end means carry string on to next line
          if newpe.msgid[-1:] == '\\':
            inmultilinemsgid = 1
            newpe.msgid = newpe.msgid[:-1]
          else:
            self.propelements.append(newpe)
            newpe = propelement()
    # see if there is a leftover one...
    if inmultilinemsgid or len(newpe.comments) > 0:
      self.propelements.append(newpe)

  def _str__(self):
    """convert the propelements back to lines"""
    lines = []
    for pe in self.propelements:
      lines.append(str(pe))
    return quote.mozillapropertiesencode("".join(lines))

  def makeindex(self):
    """makes self.index dictionary keyed on the name"""
    self.index = {}
    for pe in self.propelements:
      self.index[pe.name] = pe

if __name__ == '__main__':
  import sys
  pf = propfile(sys.stdin)
  sys.stdout.write(str(pf))

