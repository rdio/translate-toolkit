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

from __future__ import generators
import zipfile
import os.path
from translate import __version__
try:
  import cStringIO
  class NamedStringStream:
    def __init__(self, *args, **kwargs):
      self.__dict__["__i"] = cStringIO.StringIO(*args, **kwargs)
    def __getattr__(self, *args, **kwargs):
      return getattr(self.__dict__["__i"], *args, **kwargs)
  NamedStringInput = NamedStringStream
  NamedStringOutput = NamedStringStream
except ImportError:
  import StringIO
  NamedStringInput = StringIO.StringIO
  NamedStringOutput = StringIO.StringIO

# TODO: use jarfile names instead of trying to do intelligent common-prefix-stripping
# TODO: pick up lang name etc from command-line param and rename en-US to lang-reg

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

class CatchStringOutput(NamedStringOutput):
  """catches the output before it is written and sends it to an onclose method"""
  def __init__(self, onclose):
    """Set up the output stream, and remember a method to call on closing"""
    NamedStringOutput.__init__(self)
    self.onclose = onclose
  def close(self):
    """wrap the underlying close method, to pass the value to onclose before it goes"""
    value = self.getvalue()
    self.onclose(value)
    self.__dict__["__i"].close()
  def slam(self):
    """use this method to force the closing of the stream if it isn't closed yet"""
    if not self.closed:
      self.close()

class ZipFileCatcher(zipfile.ZipFile, object):
  """a ZipFile that calls any methods its instructed to before closing (useful for catching stream output)"""
  def addcatcher(self, pendingsave):
    """remember to call the given method before closing"""
    if hasattr(self, "pendingsaves"):
      self.pendingsaves.append(pendingsave)
    else:
      self.pendingsaves = [pendingsave]
  def close(self):
    """close the stream, remembering to call any addcatcher methods first"""
    if hasattr(self, "pendingsaves"):
      for pendingsave in self.pendingsaves:
        pendingsave()
    super(ZipFileCatcher, self).close()

class XpiFile(ZipFileCatcher):
  def __init__(self, *args, **kwargs):
    """sets up the xpi file"""
    self.includenonloc = kwargs.get("includenonloc", True)
    if "includenonloc" in kwargs:
      del kwargs["includenonloc"]
    super(XpiFile, self).__init__(*args, **kwargs)
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
          jarfile = ZipFileCatcher(jarstream)
          self.jarfiles[filename] = jarfile
        else:
          jarfile = self.jarfiles[filename]
        yield filename, jarfile

  def islocfile(self, filename):
    """returns whether the given file is needed for localization (basically .dtd and .properties)"""
    base, ext = os.path.splitext(filename)
    return ext in (os.extsep + "dtd", os.extsep + "properties")

  def iterjarcontents(self):
    """iterate through all the localization files stored inside the jars"""
    for jarfilename, jarfile in self.iterjars():
      for filename in jarfile.namelist():
        if filename.endswith('/'): continue
        if not self.islocfile(filename) and not self.includenonloc: continue
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
    return '/'.join(ospath.split(os.sep))

  def jartoospath(self, jarfilename, filename):
    """converts a filename from within a jarfile to an os-style filepath"""
    if jarfilename:
      jarprefix = self.jarprefixes[jarfilename]
      return self.ziptoospath(jarprefix+self.stripcommonprefix(filename))
    else:
      return self.ziptoospath(filename)

  def ostojarpath(self, ospath):
    """converts an extracted os-style filepath to a jarfilename and filename"""
    zipparts = ospath.split(os.sep)
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

  def jarfileexists(self, jarfilename, filename):
    """checks whether the given file exists inside the xpi"""
    if jarfilename is None:
      return filename in self.namelist()
    else:
      jarfile = self.jarfiles[jarfilename]
      return filename in jarfile.namelist()

  def ospathexists(self, ospath):
    """checks whether the given file exists inside the xpi"""
    jarfilename, filename = self.ostojarpath(ospath)
    if jarfilename is None:
      return filename in self.namelist()
    else:
      jarfile = self.jarfiles[jarfilename]
      return filename in jarfile.namelist()

  def openinputstream(self, jarfilename, filename):
    """opens a file (possibly inside a jarfile as a StringIO"""
    if jarfilename is None:
      contents = self.read(filename)
    else:
      jarfile = self.jarfiles[jarfilename]
      contents = jarfile.read(filename)
    inputstream = NamedStringInput(contents)
    inputstream.name = self.jartoospath(jarfilename, filename)
    if hasattr(self.fp, 'name'):
      inputstream.name = "%s:%s" % (self.fp.name, inputstream.name)
    return inputstream

  def openoutputstream(self, jarfilename, filename):
    """opens a file for writing (possibly inside a jarfile as a StringIO"""
    if jarfilename is None:
      def onclose(contents):
        self.writestr(filename, contents)
    else:
      if jarfilename in self.jarfiles:
        jarfile = self.jarfiles[jarfilename]
      else:
        jarstream = self.openoutputstream(None, jarfilename)
        jarfile = ZipFileCatcher(jarstream, "w")
        self.jarfiles[jarfilename] = jarfile
        self.addcatcher(jarstream.slam)
      def onclose(contents):
        jarfile.writestr(filename, contents)
    outputstream = CatchStringOutput(onclose)
    outputstream.name = "%s %s" % (jarfilename, filename)
    if jarfilename is None:
      self.addcatcher(outputstream.slam)
    else:
      jarfile.addcatcher(outputstream.slam)
    return outputstream

  def close(self):
    """Close the file, and for mode "w" and "a" write the ending records."""
    for jarfile in self.jarfiles.itervalues():
      jarfile.close()
    super(XpiFile, self).close()

  def iterextractnames(self, includenonjars=False, includedirs=False):
    """iterates through all the localization files with the common prefix stripped and a jarfile name added if neccessary"""
    if includenonjars:
      for filename in self.namelist():
        if filename.endswith('/') and not includedirs: continue
        if not self.islocfile(filename) and not self.includenonloc: continue
        if not filename.lower().endswith(".jar"):
          yield self.jartoospath(None, filename)
    for jarfilename, jarfile in self.iterjars():
      for filename in jarfile.namelist():
        if filename.endswith('/'):
          if not includedirs: continue
          elif len(filename.split('/'))-1 < len(self.commonprefix): continue
        if not self.islocfile(filename) and not self.includenonloc: continue
        yield self.jartoospath(jarfilename, filename)

if __name__ == '__main__':
  try:
    import optparse
  except ImportError:
    from translate.misc import optparse
  optparser = optparse.OptionParser(version="%prog "+__version__.ver)
  optparser.usage = "%prog [-l|-x] [options] file.xpi"
  optparser.add_option("-l", "--list", help="list files", \
    action="store_true", dest="listfiles", default=False)
  optparser.add_option("-x", "--extract", help="extract files", \
    action="store_true", dest="extractfiles", default=False)
  optparser.add_option("-d", "--extractdir", help="extract into EXTRACTDIR", \
    default=None, metavar="EXTRACTDIR")
  (options, args) = optparser.parse_args()
  if len(args) < 1:
    optparser.error("need at least one argument")
  xpifile = XpiFile(args[0])
  if options.listfiles:
    for name in xpifile.iterextractnames(includenonjars=True, includedirs=True):
      print name, xpifile.ostojarpath(name)
  if options.extractfiles:
    if options.extractdir and not os.path.isdir(options.extractdir):
      os.mkdir(options.extractdir)
    for name in xpifile.iterextractnames(includenonjars=True, includedirs=True):
      abspath = os.path.join(options.extractdir, name)
      if abspath.endswith(os.sep):
        if not os.path.isdir(abspath):
          os.mkdir(abspath)
        continue
      outputstream = open(abspath, 'w')
      jarfilename, filename = xpifile.ostojarpath(name)
      inputstream = xpifile.openinputstream(jarfilename, filename)
      outputstream.write(inputstream.read())
      outputstream.close()

