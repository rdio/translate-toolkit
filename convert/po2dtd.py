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

"""script that converts a .po file to a .dtd file
either done using a template or just using the .po file"""

import sys
import os
from translate.storage import dtd
from translate.storage import po
from translate.misc import quote
from translate import __version__

def findentities(definition):
  entities = {}
  amppos = 0
  while amppos != -1:
    amppos = definition.find("&",amppos)
    if amppos != -1:
      semicolonpos = definition.find(";",amppos)
      # search backwards in case there's an intervening & (if not it's OK)...
      amppos = definition.rfind("&", amppos, semicolonpos)
      if semicolonpos != -1:
        entities[definition[amppos:semicolonpos+1]] = 0
      amppos=semicolonpos
  return entities

def entitycheck(original, translation):
  originalset=findentities(original)
  translatedset=findentities(translation)
  return originalset == translatedset

def getlabel(unquotedstr):
  """retrieve the label from a mixed label+accesskey entity"""
  # mixed labels just need the & taken out
  # except that &entity; needs to be avoided...
  amppos = 0
  while amppos >= 0:
    amppos = unquotedstr.find("&",amppos)
    if amppos != -1:
      amppos += 1
      semipos = unquotedstr.find(";",amppos)
      if semipos != -1:
        if unquotedstr[amppos:semipos].isalnum():
          continue
      # otherwise, cut it out... only the first one need be changed
      # (see below to see how the accesskey is done)
      unquotedstr = unquotedstr[:amppos-1] + unquotedstr[amppos:]
      break
  return unquotedstr

def getaccesskey(unquotedstr):
  """retrieve the access key from a mixed label+accesskey entity"""
  # mixed access keys need the key extracted from after the &
  # but we must avoid proper entities i.e. &gt; etc...
  amppos = 0
  while amppos >= 0:
    amppos = unquotedstr.find("&",amppos)
    if amppos != -1:
      amppos += 1
      semipos = unquotedstr.find(";",amppos)
      if semipos != -1:
        if unquotedstr[amppos:semipos].isalnum():
          # what we have found is an entity, not a shortcut key...
          continue
      # otherwise, we found the shortcut key
      return unquotedstr[amppos]
  # if we didn't find the shortcut key, return an empty string rather than the original string
  # this will come out as "don't have a translation for this" because the string is not changed...
  # so the string from the original dtd will be used instead
  return ""

def removeinvalidamps(entity, unquotedstr):
  """find ampersands that aren't part of an entity definition..."""
  amppos = 0
  invalidamps = []
  while amppos >= 0:
    amppos = unquotedstr.find("&",amppos)
    if amppos != -1:
      amppos += 1
      semipos = unquotedstr.find(";",amppos)
      if semipos != -1:
        checkentity = unquotedstr[amppos:semipos]
        if checkentity.replace('.','').isalnum():
          # what we have found is an entity, not a problem...
          continue
        elif checkentity[0] == '#' and checkentity[1:].isalnum():
          # what we have found is an entity, not a problem...
          continue
      # otherwise, we found a problem
      invalidamps.append(amppos)
  if len(invalidamps) > 0:
    print >>sys.stderr, "ampcheck failed in %s (file %s)" % (entity, sys.argv[-1])
    comp = 0
    for amppos in invalidamps:
      unquotedstr = unquotedstr[:amppos-comp] + unquotedstr[amppos-comp+1:]
      comp += 1
  return unquotedstr

def extractpoline(line):
  backslash = '\\'
  return quote.extractwithoutquotes(line,'"','"',backslash,includeescapes=0)[0]

def dounquotepo(thepo):
  unquotedid = "\n".join([extractpoline(line) for line in thepo.msgid])
  if unquotedid[:1] == "\n":
    unquotedid = unquotedid[1:]
  unquotedstr = "\n".join([extractpoline(line) for line in thepo.msgstr])
  if unquotedstr[:1] == "\n":
    unquotedstr = unquotedstr[1:]
  return unquotedid, unquotedstr

def getmixedentities(entities):
  """returns a list of mixed .label and .accesskey entities from a list of entities"""
  mixedentities = []  # those entities which have a .label and .accesskey combined
  # search for mixed entities...
  for entity in entities:
    if entity.endswith(".label"):
      entitybase = entity[:entity.rfind(".label")]
      # see if there is a matching accesskey, making this a mixed entity
      if entitybase + ".accesskey" in entities:
        # add both versions to the list of mixed entities
        mixedentities += [entity,entitybase+".accesskey"]
  return mixedentities

def applytranslation(entity, thedtd, thepo, mixedentities):
  """applies the translation for entity in the po element to the dtd element"""
  # this converts the po-style string to a dtd-style string
  unquotedid, unquotedstr = dounquotepo(thepo)
  # check there aren't missing entities...
  if len(unquotedstr.strip()) == 0:
    return
  if not entitycheck(unquotedid, unquotedstr):
    # print to stderr that the entities in the original and translation don't match
    print >>sys.stderr, "entitycheck failed in %s (file %s)" % (entity, sys.argv[-1])
    print >>sys.stderr, "  unquotedid: %r" % unquotedid
    print >>sys.stderr, "  unquotedstr: %r" % unquotedstr
    # we could alternatively make it the same as the original
    # we lose the translation, but we avoid crash-type errors
    # unquotedstr = unquotedid
  # handle mixed entities
  if entity.endswith(".label"):
    if entity in mixedentities:
      unquotedstr = getlabel(unquotedstr)
  elif entity.endswith(".accesskey"):
    if entity in mixedentities:
      unquotedstr = getaccesskey(unquotedstr)
  elif entity.endswith(".size"):
    if unquotedstr != unquotedid:
      print >>sys.stderr, "warning: size may have changed in %s (file %s)" % (entity, sys.argv[-1])
  # handle invalid left-over ampersands (usually unneeded access key shortcuts)
  unquotedstr = removeinvalidamps(entity, unquotedstr)
  # finally set the new definition in the dtd, but not if its empty
  if len(unquotedstr) > 0:
    thedtd.definition = quote.doencode(quote.eitherquotestr(unquotedstr))

class redtd:
  """this is a convertor class that creates a new dtd based on a template using translations in a po"""
  def __init__(self, dtdfile):
    self.dtdfile = dtdfile

  def convertfile(self, pofile):
    # translate the strings
    for thepo in pofile.poelements:
      # there may be more than one entity due to msguniq merge
      self.handlepoelement(thepo)
    return self.dtdfile

  def handlepoelement(self, thepo):
    entities = thepo.getsources()
    mixedentities = getmixedentities(entities)
    for entity in entities:
      if self.dtdfile.index.has_key(entity):
        # now we need to replace the definition of entity with msgstr
        thedtd = self.dtdfile.index[entity] # find the dtd
        applytranslation(entity, thedtd, thepo, mixedentities)

class po2dtd:
  """this is a convertor class that creates a new dtd file based on a po file without a template"""
  def convertcomments(self,thepo,thedtd):
    # get the entity from sourcecomments
    entitiesstr = " ".join([sourcecomment[2:].strip() for sourcecomment in thepo.sourcecomments])
    #  # entitystr, instring = quote.extract(sourcecomment, "#:","\n",None)
    #  entitiesstr += sourcecomment[2:].strip()
    entities = entitiesstr.split()
    if len(entities) > 1:
      # don't yet handle multiple entities
      thedtd.comments.append(("conversionnote",'<!-- CONVERSION NOTE - multiple entities -->\n'))
      thedtd.entity = entities[0]
    elif len(entities) == 1:
      thedtd.entity = entities[0]
    else:
      # this produces a blank entity, which doesn't write anything out
      thedtd.entity = ""

     # typecomments are for example #, fuzzy
    types = []
    for typecomment in thepo.typecomments:
      # typestr, instring = quote.extract(typecomment, "#,","\n",None)
      types.append(quote.unstripcomment(typecomment[2:]))
    for typedescr in types:
      thedtd.comments.append(("potype",quote.doencode(typedescr+'\n')))
    # visiblecomments are for example #_ note to translator
    visibles = []
    for visiblecomment in thepo.visiblecomments:
      # visiblestr, instring = quote.extract(visiblecomment,"#_","\n",None)
      visibles.append(quote.unstripcomment(visiblecomment[2:]))
    for visible in visibles:
      thedtd.comments.append(("visible",quote.doencode(visible+'\n')))
    # othercomments are normal e.g. # another comment
    others = []
    for othercomment in thepo.othercomments:
      # otherstr, instring = quote.extract(othercomment,"#","\n",None)
      others.append(quote.unstripcomment(othercomment[2:]))
    for other in others:
      # don't put in localization note group comments as they are artificially added
      if (other.find('LOCALIZATION NOTE') == -1) or (other.find('GROUP') == -1):
        thedtd.comments.append(("comment",quote.doencode(other)))
    # msgidcomments are special - they're actually localization notes
    for msgidcomment in thepo.msgidcomments:
      unquotedmsgidcomment = quote.extractwithoutquotes(msgidcomment,'"','"','\\',includeescapes=0)[0]
      actualnote = unquotedmsgidcomment.replace("_:","",1)
      if actualnote[-2:] == '\\n':
        actualnote = actualnote[:-2]
      locnote = quote.unstripcomment("LOCALIZATION NOTE ("+thedtd.entity+"): "+actualnote)
      thedtd.comments.append(("locnote",quote.doencode(locnote)))

  def convertstrings(self,thepo,thedtd):
    # currently let's just get the msgid back
    backslash = '\\'
    unquotedid = "\n".join([quote.extractwithoutquotes(line,'"','"',backslash,includeescapes=0)[0] for line in thepo.msgid])
    if unquotedid[:1] == "\n": unquotedid = unquotedid[1:]
    unquotedstr = "\n".join([quote.extractwithoutquotes(line,'"','"',backslash,includeescapes=0)[0] for line in thepo.msgstr])
    if unquotedstr[:1] == "\n": unquotedstr = unquotedstr[1:]
    # choose the msgstr unless it's empty, in which case choose the msgid
    if len(unquotedstr) == 0:
      unquoted = unquotedid
    else:
      unquoted = unquotedstr
    thedtd.definition = quote.doencode(quote.eitherquotestr(unquoted))

  def convertelement(self,thepo):
    thedtd = dtd.dtdelement()
    self.convertcomments(thepo,thedtd)
    self.convertstrings(thepo,thedtd)
    return thedtd

  def convertfile(self,thepofile):
    thedtdfile = dtd.dtdfile()
    self.currentgroups = []
    for thepo in thepofile.poelements:
      thedtd = self.convertelement(thepo)
      if thedtd is not None:
        thedtdfile.dtdelements.append(thedtd)
    return thedtdfile

def convertfile(inputfile, outputfile, templatefile):
  inputpo = po.pofile(inputfile)
  if templatefile is None:
    convertor = po2dtd()
  else:
    templatedtd = dtd.dtdfile(templatefile)
    convertor = redtd(templatedtd)
  outputdtd = convertor.convertfile(inputpo)
  outputdtdlines = outputdtd.tolines()
  outputfile.writelines(outputdtdlines)

inputformat = "po"
outputformat = "dtd"
templateformat = "dtd"

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
        # only handle names that match the correct extension...
        base, inputext = os.path.splitext(name)
        if inputext != os.extsep + inputformat:
          print >>sys.stderr, "not processing %s: wrong extension (%r != %r)" % (name, inputext, inputformat)
          continue
        outputname = os.path.join(outputdir, top, base) + os.extsep + outputformat
        inputfile = open(inputname, 'r')
        outputfile = open(outputname, 'w')
        templatefile = None
        if templatedir is not None:
          templatename = os.path.join(templatedir, top, base) + os.extsep + templateformat
          if os.path.isfile(templatename):
            templatefile = open(templatename, 'r')
          else:
            print >>sys.stderr, "warning: missing template file %s" % templatename
        convertfile(inputfile, outputfile, templatefile)
    # make sure the directories are processed next time round...
    dirs.reverse()
    dirstack.extend(dirs)

def handleoptions(options):
  """handles the options, allocates files, and runs the neccessary functions..."""
  if options.recursive:
    if options.inputfile is None:
      raise optparse.OptionValueError("cannot use stdin for recursive run. please specify inputfile")
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
  else:
    if options.inputfile is None:
      inputfile = sys.stdin
    else:
      inputfile = open(options.inputfile, 'r')
    if options.outputfile is None:
      outputfile = sys.stdout
    else:
      outputfile = open(options.outputfile, 'w')
    if options.templatefile is None:
      templatefile = None
    else:
      templatefile = open(options.templatefile, 'r')
    convertfile(inputfile, outputfile, templatefile)

if __name__ == '__main__':
  # handle command line options
  try:
    import optparse
  except ImportError:
    from translate.misc import optparse
  parser = optparse.OptionParser(usage="%prog [options] [-i|--input-file inputfile] [-o|--output-file outputfile] [-t|--template templatefile]",
                                 version="%prog "+__version__.ver)
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

