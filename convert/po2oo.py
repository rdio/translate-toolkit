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
    if len(groupid) == 0 or len(localid) == 0:
      fullid = groupid + localid
    else:
      fullid = groupid + "." + localid
    key = "%s/%s:%s" % (project, sourcefile, fullid)
    return key.replace(" ","_")

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

def getmtime(filename):
  import stat
  return time.localtime(os.stat(filename)[stat.ST_MTIME])

def convertoo(inputfile, outputfile, templatefile):
  inputpo = po.pofile()
  inputpo.fromlines(inputfile.readlines())
  if templatefile is None:
    raise ValueError("must have template file for oo files")
    # convertor = po2oo()
  else:
    convertor = reoo(templatefile)
  outputoo = convertor.convertfile(inputpo)
  outputoolines = outputoo.tolines()
  outputfile.writelines(outputoolines)

inputformat = "po"
outputformat = "oo"
templateformat = "oo"

def recurse(inputdir, outputdir, templatedir):
  dirstack = ['']
  while dirstack:
    top = dirstack.pop(-1)
    names = os.listdir(os.path.join(inputdir, top))
    dirs = []
    for name in names:
      inputname = os.path.join(inputdir, top, name)
      # handle directories...
      if os.path.isdir(inputname):
        dirs.append(os.path.join(top, name))
        outputname = os.path.join(outputdir, top, name)
        if not os.path.isdir(outputname):
          os.mkdir(outputname)
        if templatedir is not None:
          templatename = os.path.join(templatedir, top, name)
          if not os.path.isdir(templatename):
            print >>sys.stderr, "warning: missing template directory %s" % templatename
      elif os.path.isfile(inputname):
        base, inputext = os.path.splitext(name)
        if inputext != os.extsep + inputformat:
          # only handle names that match the correct input file extension
          continue
        # now we have split off .po, we split off the original extension
        outputbase, outputext = os.path.splitext(base)
        outputname = os.path.join(outputdir, top, base)
        outputext = outputext.replace(os.extsep, "", 1)
        if outputext != outputformat:
          print >>sys.stderr, "not processing %s: unknown extension (%s)" % (name, outputext)
          continue
        inputfile = open(inputname, 'r')
        outputfile = open(outputname, 'w')
        templatefile = None
        if templatedir is not None:
          templatename = os.path.join(templatedir, top, base)
          if os.path.isfile(templatename):
            templatefile = open(templatename, 'r')
          else:
            print >>sys.stderr, "warning: missing template file %s" % templatename
        convertoo(inputfile, outputfile, templatefile)
    # make sure the directories are processed next time round...
    dirs.reverse()
    dirstack.extend(dirs)

def handleoptions(options):
  """handles the options, and runs the neccessary functions..."""
  if options.inputfile is None:
    raise optparse.OptionValueError("cannot use stdin for recursive run. please specify inputdir")
  if not os.path.isdir(options.inputfile):
    raise optparse.OptionValueError("inputfile must be directory for recursive run.")
  if options.outputfile is None:
    raise optparse.OptionValueError("must specify output directory for recursive run.")
  if not os.path.isdir(options.outputfile):
    raise optparse.OptionValueError("output must be existing directory for recursive run.")
  if options.templatefile is not None:
    if not os.path.isdir(options.templatefile):
      raise optparse.OptionValueError("template must be existing directory for recursive run.")
  recurse(options.inputfile, options.outputfile, options.templatefile)

if __name__ == '__main__':
  # handle command line options
  try:
    import optparse
  except ImportError:
    from translate.misc import optparse
  parser = optparse.OptionParser(usage="%prog [options] [-i|--input-file inputfile] [-o|--output-file outputfile] [-t|--template templatefile]")
  parser.add_option("-R", "--recursive", action="store_true", dest="recursive", default=False, help="recurse subdirectories")
  parser.add_option("-i", "--input-file", dest="inputfile", default=None,
                    help="read from inputfile in "+inputformat+" format", metavar="inputfile")
  parser.add_option("-o", "--output-file", dest="outputfile", default=None,
                    help="write to outputfile in "+outputformat+" format", metavar="outputfile")
  parser.add_option("-t", "--template", dest="templatefile", default=None,
                    help="read from template in "+templateformat+" format", metavar="template")
  (options, args) = parser.parse_args()
  # open the appropriate files
  try:
    handleoptions(options)
  except optparse.OptParseError, message:
    parser.error(message)

