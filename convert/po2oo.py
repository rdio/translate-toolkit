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

def extractpoline(line):
  backslash = '\\'
  extracted = quote.extractwithoutquotes(line,'"','"',backslash,includeescapes=1)[0]
  return extracted.replace('\\"', '"')

def dounquotepo(thepo):
  unquotedid = "\n".join([extractpoline(line) for line in thepo.msgid])
  if unquotedid[:1] == "\n":
    unquotedid = unquotedid[1:]
  unquotedstr = "\n".join([extractpoline(line) for line in thepo.msgstr])
  if unquotedstr[:1] == "\n":
    unquotedstr = unquotedstr[1:]
  return unquotedid, unquotedstr

class reoo:
  def __init__(self, templatefile, languages=None, timestamp=None):
    """construct a reoo converter for the specified languages"""
    # languages is a pair of language ids
    self.readoo(templatefile)
    self.languages = languages
    if timestamp is None:
      self.timestamp = time.localtime(time.time())
    else:
      self.timestamp = timestamp
    self.timestamp_str = time.strftime("%Y%m%d %H:%M:%S", self.timestamp)

  def makekey(self, ookey):
    """converts an oo key tuple into a key identifier for the po file"""
    project, sourcefile, resourcetype, groupid, localid, platform = ookey
    sourcefile = sourcefile.replace('\\','/')
    if len(groupid) == 0 or len(localid) == 0:
      fullid = groupid + localid
    else:
      fullid = groupid + "." + localid
    key = "%s/%s#%s" % (project, sourcefile, fullid)
    return oo.normalizefilename(key)

  def makeindex(self):
    """makes an index of the oo keys that are used in the po file"""
    self.index = {}
    for ookey, theoo in self.o.ookeys.iteritems():
      pokey = self.makekey(ookey)
      self.index[pokey] = theoo

  def readoo(self, of):
    """read in the oo from the file"""
    oolines = of.readlines()
    self.o = oo.oofile()
    self.o.fromlines(oolines)
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
        print >>sys.stderr, "couldn't find key %r in po %s" % (key, "\n".join(thepo.tolines()))

  def applytranslation(self, key, subkey, theoo, thepo):
    """applies the translation for entity in the po element to the dtd element"""
    if self.languages is None:
      part1 = theoo.lines[0]
      part2 = theoo.lines[1]
    else:
      part1 = theoo.languages[self.languages[0]]
      part2 = theoo.languages[self.languages[1]]
    # this converts the po-style string to a dtd-style string
    unquotedid, unquotedstr = dounquotepo(thepo)
    # check there aren't missing entities...
    if len(unquotedstr.strip()) == 0:
      return
    # finally set the new definition in the oo, but not if its empty
    if len(unquotedstr) > 0:
      setattr(part2, subkey, unquotedstr)
    # set the modified time
    part2.timestamp = self.timestamp_str

  def convertfile(self, inputpo):
    self.p = inputpo
    # translate the strings
    for thepo in self.p.poelements:
      # there may be more than one element due to msguniq merge
      self.handlepoelement(thepo)
    # return the modified oo file object
    return self.o

  def renumberdest(self, newcode):
    """change the language code oldcode to newcode"""
    for theooelement in self.o.ooelements:
      theooline = theooelement.lines[1]
      theooline.languageid = newcode

def getmtime(filename):
  import stat
  return time.localtime(os.stat(filename)[stat.ST_MTIME])

def convertoo(inputfile, outputfile, templatefile, languagecode=None):
  inputpo = po.pofile()
  inputpo.fromlines(inputfile.readlines())
  if templatefile is None:
    raise ValueError("must have template file for oo files")
    # convertor = po2oo()
  else:
    convertor = reoo(templatefile)
  outputoo = convertor.convertfile(inputpo)
  if languagecode is not None:
    convertor.renumberdest(languagecode)
  outputoolines = outputoo.tolines()
  outputfile.writelines(outputoolines)
  return True

if __name__ == '__main__':
  # handle command line options
  from translate.convert import convert
  inputformats = {"po":convertoo}
  outputformat = "oo"
  templateformat = "oo"
  parser = convert.ConvertOptionParser(convert.optionalrecursion, inputformats, outputformat, usetemplates=True, templateslikeinput=False)
  parser.add_option("-l", "--language-code", dest="languagecode", default=None, 
                    help="set language code of destination (e.g. 27, 99)", metavar="languagecode")
  (options, args) = parser.parse_args()
  try:
    parser.runconversion(options, convertoo)
  except convert.optparse.OptParseError, message:
    parser.error(message)

