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

def _commonprefix(itemlist):
  def cp(a, b):
    l = min(len(a), len(b))
    for n in range(l):
      if a[n] != b[n]: return a[:n]
    return a[:l]
  if itemlist:
    return reduce(cp, itemlist)
  else:
    return ''

class XpiFile(zipfile.ZipFile):
  def __init__(self, *args, **kwargs):
    """sets up the xpi file"""
    zipfile.ZipFile.__init__(self, *args, **kwargs)
    self.jarfiles = {}
    self.commonprefix = self.findcommonprefix()
    self.jarprefixes = self.findjarprefixes()
    self.reverseprefixes = dict([
      (prefix,jarfilename) for jarfilename, prefix in self.jarprefixes.iteritems() if prefix])

  def iterjars(self):
    """iterate through the jar files in the xpi as ZipFile objects"""
    for filename in self.namelist():
      if filename.lower().endswith('.jar'):
        if filename not in self.jarfiles:
          jarstream = self.openinputstream(None, filename)
          jarfile = zipfile.ZipFile(jarstream)
          self.jarfiles[filename] = jarfile
        else:
          jarfile = self.jarfiles[filename]
        yield filename, jarfile

  def iterjarcontents(self):
    """iterate through all the localization files stored inside the jars"""
    for jarfilename, jarfile in self.iterjars():
      for filename in jarfile.namelist():
        if filename.endswith('/'): continue
        yield filename

  def findcommonprefix(self):
    """finds the common prefix of all the files stored in the jar files"""
    return _commonprefix([filename.split('/') for filename in self.iterjarcontents()])

  def stripcommonprefix(self, filename):
    """strips the common prefix off the filename"""
    fileparts = filename.split('/')
    fileprefix = fileparts[:len(self.commonprefix)]
    if fileprefix != self.commonprefix:
      raise ValueError("cannot strip commonprefix %r from filename %r" % (self.commonprefix, filename))
    return '/'.join(fileparts[len(self.commonprefix):])

  def findjarprefixes(self):
    """checks the uniqueness of the jar files contents"""
    uniquenames = {}
    jarprefixes = {}
    for jarfilename, jarfile in self.iterjars():
      jarprefixes[jarfilename] = ""
      for filename in jarfile.namelist():
        if filename.endswith('/'): continue
        if filename in uniquenames:
          jarprefixes[jarfilename] = True
          jarprefixes[uniquenames[filename]] = True
        else:
          uniquenames[filename] = jarfilename
    for jarfilename, hasconflicts in jarprefixes.items():
      if hasconflicts:
        shortjarfilename = os.path.split(jarfilename)[1]
        shortjarfilename = os.path.splitext(shortjarfilename)[0]
        jarprefixes[jarfilename] = shortjarfilename+'/'
    # this is a clever trick that will e.g. remove zu- from zu-win, zu-mac, zu-unix
    commonjarprefix = _commonprefix([prefix for prefix in jarprefixes.itervalues() if prefix])
    if commonjarprefix:
      for jarfilename, prefix in jarprefixes.items():
        if prefix:
          jarprefixes[jarfilename] = prefix.replace(commonjarprefix, '', 1)
    return jarprefixes

  def ziptoospath(self, zippath):
    """converts a zipfile filepath to an os-style filepath"""
    return os.path.join(*zippath.split('/'))

  def ostozippath(self, ospath):
    """converts an os-style filepath to a zipfile filepath"""
    return '/'.join(ospath.split(os.path.sep))

  def jartoospath(self, jarfilename, filename):
    """converts a filename from within a jarfile to an os-style filepath"""
    if jarfilename:
      jarprefix = self.jarprefixes[jarfilename]
      return self.ziptoospath(jarprefix+self.stripcommonprefix(filename))
    else:
      return self.ziptoospath(filename)

  def ostojarpath(self, ospath):
    """converts an extracted os-style filepath to a jarfilename and filename"""
    zipparts = ospath.split(os.path.sep)
    prefix = zipparts[0] + '/'
    if prefix in self.reverseprefixes:
      jarfilename = self.reverseprefixes[prefix]
      filename = '/'.join(self.commonprefix + zipparts[1:])
      return jarfilename, filename
    else:
      filename = self.ostozippath(ospath)
      if filename in self.namelist():
        return None, filename
      filename = '/'.join(self.commonprefix + zipparts)
      possiblejarfilenames = [jarfilename for jarfilename, prefix in self.jarprefixes.iteritems() if not prefix]
      for jarfilename in possiblejarfilenames:
        jarfile = self.jarfiles[jarfilename]
        if filename in jarfile.namelist():
          return jarfilename, filename
      raise IndexError("ospath not found in xpi file, could not guess location: %r" % ospath)

  def openinputstream(self, jarfilename, filename):
    """opens a file (possibly inside a jarfile as a StringIO"""
    if jarfilename is None:
      contents = self.read(filename)
    else:
      jarfile = self.jarfiles[jarfilename]
      contents = jarfile.read(filename)
    return StringIO(contents)

  def iterextractnames(self, includenonjars=False, includedirs=False):
    """iterates through all the localization files with the common prefix stripped and a jarfile name added if neccessary"""
    if includenonjars:
      for filename in self.namelist():
        if filename.endswith('/') and not includedirs: continue
        if not filename.lower().endswith(".jar"):
          yield self.jartoospath(None, filename)
    for jarfilename, jarfile in self.iterjars():
      for filename in jarfile.namelist():
        if filename.endswith('/'):
          if not includedirs: continue
          elif len(filename.split('/'))-1 < len(self.commonprefix): continue
        yield self.jartoospath(jarfilename, filename)

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
  for name in x.iterextractnames(True, True):
    print name, x.ostojarpath(name)

