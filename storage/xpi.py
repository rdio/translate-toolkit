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

"""module for accessing mozilla xpi packages"""

import zipfile
import os.path
from translate import __version__
try:
  from cStringIO import StringIO
except:
  from StringIO import StringIO

class XpiFile(zipfile.ZipFile):
  def iterjars(self):
    """iterate through the jar files in the xpi as ZipFile objects"""
    for filename in self.namelist():
      if filename.lower().endswith('.jar'):
        jarcontents = self.read(filename)
        jarstream = StringIO(jarcontents)
        jarfile = zipfile.ZipFile(jarstream)
        yield filename, jarfile

  def commonprefix(self):
    """finds the common prefix of all the files stored in the jar files"""
    filelist = []
    for filename in self.iterfilenames():
      filelist.append(filename.split('/'))
    def cp(a, b):
      l = min(len(a), len(b))
      for n in range(l):
        if a[n] != b[n]: return a[:n]
      return a[:l]
    return reduce(cp, filelist)

  def iterfilenames(self):
    """iterate through all the localization files stored inside the jars"""
    for jarfilename, jarfile in self.iterjars():
      for filename in jarfile.namelist():
        if filename.endswith('/'): continue
        yield filename

  def iterextractnames(self, includenonjars=False):
    """iterates through all the localization files with the common prefix stripped and a jarfile name added if neccessary"""
    jarcontents = {}
    uniquenames = {}
    hasconflicts = {}
    if includenonjars:
      nonjarfilelist = []
      for filename in self.namelist():
        if filename.endswith('/'): continue
        if not filename.lower().endswith(".jar"):
          nonjarfilelist.append(filename.split('/'))
      jarcontents[None] = nonjarfilelist
    cplen = len(self.commonprefix())
    for jarfilename, jarfile in self.iterjars():
      jarfilelist = []
      for filename in jarfile.namelist():
        if filename.endswith('/'): continue
        if filename in uniquenames:
          hasconflicts[jarfilename] = True
          hasconflicts[uniquenames[filename]] = True
        else:
          uniquenames[filename] = jarfilename
        fileparts = filename.split('/')
        jarfilelist.append(fileparts[cplen:])
      jarcontents[jarfilename] = jarfilelist
    for jarfilename, jarfilelist in jarcontents.iteritems():
      if jarfilename in hasconflicts:
        jarprefix = jarfilename[:jarfilename.lower().rfind('.jar')]
        for fileparts in jarfilelist:
          yield os.path.join(jarprefix, *fileparts)
      else:
        for fileparts in jarfilelist:
          yield os.path.join(*fileparts)

if __name__ == '__main__':
  try:
    import optparse
  except ImportError:
    from translate.misc import optparse
  optparser = optparse.OptionParser(version="%prog "+__version__.ver)
  (options, args) = optparser.parse_args()
  if len(args) < 1:
    optparser.error("need at least one argument")
  else:
    x = XpiFile(args[0])
  x.printdir()
  for name in x.iterextractnames():
    print name

