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
#

"""script that converts a .po file with translations based on a .pot file
generated from a OpenOffice localization .oo back to the .oo (but translated)
Uses the original .oo to do the conversion as this makes sure we don't
leave out any unincluded stuff..."""

import sys
import os
from translate.storage import oo
from translate.storage import po
from translate.misc import quote
import time
from translate import __version__

class reoo:
  def __init__(self, templatefile, languages=None, timestamp=None, includefuzzy=False, long_keys=False):
    """construct a reoo converter for the specified languages (timestamp=0 means leave unchanged)"""
    # languages is a pair of language ids
    self.long_keys = long_keys
    self.readoo(templatefile)
    self.languages = languages
    if timestamp is None:
      self.timestamp = time.localtime(time.time())
    else:
      self.timestamp = timestamp
    if self.timestamp:
      self.timestamp_str = time.strftime("%Y%m%d %H:%M:%S", self.timestamp)
    else:
      self.timestamp_str = None
    self.includefuzzy = includefuzzy

  def makekey(self, ookey):
    """converts an oo key tuple into a key identifier for the po file"""
    project, sourcefile, resourcetype, groupid, localid, platform = ookey
    sourcefile = sourcefile.replace('\\','/')
    if self.long_keys:
      sourcebase = os.path.join(project, sourcefile)
    else:
      sourceparts = sourcefile.split('/')
      sourcebase = "".join(sourceparts[-1:])
    if len(groupid) == 0 or len(localid) == 0:
      fullid = groupid + localid
    else:
      fullid = groupid + "." + localid
    if resourcetype:
      fullid = fullid + "." + resourcetype
    key = "%s#%s" % (sourcebase, fullid)
    return oo.normalizefilename(key)

  def makeindex(self):
    """makes an index of the oo keys that are used in the po file"""
    self.index = {}
    for ookey, theoo in self.o.ookeys.iteritems():
      pokey = self.makekey(ookey)
      self.index[pokey] = theoo

  def readoo(self, of):
    """read in the oo from the file"""
    oosrc = of.read()
    self.o = oo.oofile()
    self.o.parse(oosrc)
    self.makeindex()

  def handlepoelement(self, thepo):
    # TODO: make this work for multiple columns in oo...
    sources = thepo.getsources()
    # technically our formats should just have one source for each entry...
    # but we handle multiple ones just to be safe...
    for source in sources:
      subkeypos = source.rfind('.')
      subkey = source[subkeypos+1:]
      key = source[:subkeypos]
      # this is just to handle our old system of using %s/%s:%s instead of %s/%s#%s
      key = key.replace(':', '#')
      # this is to handle using / instead of \ in the sourcefile...
      key = key.replace('\\', '/')
      key = oo.normalizefilename(key)
      if self.index.has_key(key):
        # now we need to replace the definition of entity with msgstr
        theoo = self.index[key] # find the oo
        self.applytranslation(key, subkey, theoo, thepo)
      else:
        print >>sys.stderr, "couldn't find key %r in po:" % key
        try:
          polines = str(thepo)
          if isinstance(polines, unicode):
            polines = polines.encode("utf-8")
          print >>sys.stderr, polines
        except:
          print >>sys.stderr, "error outputting po %r" % (str(thepo),)

  def applytranslation(self, key, subkey, theoo, thepo):
    """applies the translation for entity in the po element to the dtd element"""
    if not self.includefuzzy and thepo.isfuzzy():
      return
    makecopy = False
    if self.languages is None:
      part1 = theoo.lines[0]
      if len(theoo.lines) > 1:
        part2 = theoo.lines[1]
      else:
        makecopy = True
    else:
      part1 = theoo.languages[self.languages[0]]
      if self.languages[1] in theoo.languages:
        part2 = theoo.languages[self.languages[1]]
      else:
        makecopy = True
    if makecopy:
      part2 = oo.ooline(part1.getparts())
    # this converts the po-style string to a dtd-style string
    unquotedid = po.unquotefrompo(thepo.msgid, joinwithlinebreak=False)
    unquotedstr = po.unquotefrompo(thepo.msgstr, joinwithlinebreak=False)
    # check there aren't missing entities...
    if len(unquotedstr.strip()) == 0:
      return
    if isinstance(unquotedstr, unicode):
      unquotedstr = unquotedstr.encode("UTF-8")
    # finally set the new definition in the oo, but not if its empty
    if len(unquotedstr) > 0:
      setattr(part2, subkey, unquotedstr)
    # set the modified time
    if self.timestamp_str:
      part2.timestamp = self.timestamp_str
    if self.languages:
      part2.languageid = self.languages[1]
    if makecopy:
      theoo.addline(part2)

  def convertfile(self, inputpo):
    self.p = inputpo
    # translate the strings
    for thepo in self.p.elements:
      # there may be more than one element due to msguniq merge
      self.handlepoelement(thepo)
    # return the modified oo file object
    return self.o

def getmtime(filename):
  import stat
  return time.localtime(os.stat(filename)[stat.ST_MTIME])

def convertoo(inputfile, outputfile, templatefile, sourcelanguage=None, targetlanguage=None, timestamp=None, includefuzzy=False, multifilestyle="single"):
  inputpo = po.pofile()
  inputpo.parse(inputfile.read())
  if not targetlanguage:
    raise ValueError("You must specify the target language")
  if not sourcelanguage:
    if targetlanguage.isdigit():
      sourcelanguage = "01"
    else:
      sourcelanguage = "en-US"
  languages = (sourcelanguage, targetlanguage)
  if templatefile is None:
    raise ValueError("must have template file for oo files")
    # convertor = po2oo()
  else:
    convertor = reoo(templatefile, languages=languages, timestamp=timestamp, includefuzzy=includefuzzy, long_keys=multifilestyle != "single")
  outputoo = convertor.convertfile(inputpo)
  # TODO: check if we need to manually delete missing items
  outputoosrc = str(outputoo)
  outputfile.write(outputoosrc)
  return True

def main():
  from translate.convert import convert
  formats = {("po", "oo"):("oo", convertoo)}
  # always treat the input as an archive unless it is a directory
  archiveformats = {(None, "output"): oo.oomultifile, (None, "template"): oo.oomultifile}
  parser = convert.ArchiveConvertOptionParser(formats, usetemplates=True, description=__doc__, archiveformats=archiveformats)
  parser.add_option("-l", "--language", dest="targetlanguage", default=None, 
                    help="set target language code (e.g. af-ZA) [required]", metavar="LANG")
  parser.add_option("", "--source-language", dest="sourcelanguage", default=None, 
                    help="set source language code (default en-US)", metavar="LANG")
  parser.add_option("-T", "--keeptimestamp", dest="timestamp", default=None, action="store_const", const=0,
                    help="don't change the timestamps of the strings")
  parser.add_option("", "--nonrecursiveoutput", dest="allowrecursiveoutput", default=True, action="store_false", help="don't treat the output oo as a recursive store")
  parser.add_option("", "--nonrecursivetemplate", dest="allowrecursivetemplate", default=True, action="store_false", help="don't treat the template oo as a recursive store")
  parser.add_fuzzy_option()
  parser.add_multifile_option()
  parser.passthrough.append("sourcelanguage")
  parser.passthrough.append("targetlanguage")
  parser.passthrough.append("timestamp")
  parser.run()

