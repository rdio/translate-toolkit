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

"""script to convert a mozilla .dtd localization format to a
gettext .po localization file using the po and dtd modules, and the 
dtd2po convertor class which is in this module
You can convert back to .dtd using po2dtd.py"""

import sys
from translate.storage import po
from translate.storage import dtd
from translate.misc import quote
from translate import __version__

class dtd2po:
  def __init__(self):
    self.currentgroup = None 

  def convertcomments(self,thedtd,thepo):
    entity = quote.rstripeol(thedtd.entity)
    if len(entity) > 0:
      thepo.sourcecomments.append("#: " + thedtd.entity + "\n")
    for commenttype,comment in thedtd.comments:
      # handle groups
      if (commenttype == "locgroupstart"):
        groupcomment = comment.replace('BEGIN','GROUP')
        self.currentgroup = groupcomment
      elif (commenttype == "locgroupend"):
        groupcomment = comment.replace('END','GROUP')
        self.currentgroup = None
      # handle msgidcomments
      if commenttype == "msgidcomment":
        thepo.msgidcomments.append(comment + "\n")
      # handle normal comments
      else:
        thepo.visiblecomments.append("# " + quote.stripcomment(comment) + "\n")
    # handle group stuff
    if self.currentgroup is not None:
      thepo.visiblecomments.append("# " + quote.stripcomment(self.currentgroup) + "\n")  

  def extractdtdstring(self,dtdstring):
    # extract the string, get rid of quoting
    if len(dtdstring) == 0: dtdstring = '""'
    quotechar = dtdstring[0]
    extracted,quotefinished = quote.extract(dtdstring,quotechar,quotechar,None)
    # the quote characters should be the first and last characters in the string
    # of course there could also be quote characters within the string; not handled here
    return extracted[1:-1]

  def convertstrings(self,thedtd,thepo):
    # extract the string, get rid of quoting
    unquoted = self.extractdtdstring(thedtd.definition)
    # escape backslashes...
    unquoted = unquoted.replace("\\", "\\\\")
    # now split the string into lines and quote them
    msgid = [quote.quotestr(line) for line in unquoted.split('\n')]
    thepo.msgid = msgid
    thepo.msgstr = ['""']

  def convertmixedelement(self,labeldtd,accesskeydtd):
    labelpo = self.convertelement(labeldtd)
    accesskeypo = self.convertelement(accesskeydtd)
    thepo = po.poelement()
    thepo.sourcecomments += labelpo.sourcecomments
    thepo.sourcecomments += accesskeypo.sourcecomments
    thepo.msgidcomments += labelpo.msgidcomments
    thepo.msgidcomments += accesskeypo.msgidcomments
    thepo.visiblecomments += labelpo.visiblecomments
    thepo.visiblecomments += accesskeypo.visiblecomments
    # redo the strings from original dtd...
    label = self.extractdtdstring(labeldtd.definition)
    accesskey = self.extractdtdstring(accesskeydtd.definition)
    if len(accesskey) == 0:
      return None
    # try and put the & in front of the accesskey in the label...
    # make sure to avoid muddling up &amp;-type strings
    searchpos = 0
    accesskeypos = -1
    inentity = 0
    accesskeyaltcasepos = -1
    while (accesskeypos < 0) and searchpos < len(label):
      searchchar = label[searchpos]
      if searchchar == '&':
        inentity = 1
      elif searchchar == ';':
        inentity = 0
      else:
        if not inentity:
          if searchchar == accesskey.upper():
            # always prefer uppercase
            accesskeypos = searchpos
          if searchchar == accesskey.lower():
            # take lower case otherwise...
            if accesskeyaltcasepos == -1:
              # only want to remember first altcasepos
              accesskeyaltcasepos = searchpos
              # note: we keep on looping through in hope of exact match
      searchpos += 1

    # if we didn't find an exact case match, use an alternate one if available
    if accesskeypos == -1:
      accesskeypos = accesskeyaltcasepos
    # now we want to handle whatever we found...
    if accesskeypos >= 0:
      label = label[:accesskeypos] + '&' + label[accesskeypos:]
    else:
      # can't currently mix accesskey if it's not in label
      return None
    # now split the string into lines and quote them, like in convertstrings
    msgid = [quote.quotestr(line) for line in label.split('\n')]
    thepo.msgid = msgid
    thepo.msgstr = ['""']
    return thepo

  def convertelement(self,thedtd):
    thepo = po.poelement()

    # remove unwanted stuff
    for commentnum in range(len(thedtd.comments)):
      commenttype,locnote = thedtd.comments[commentnum]
      # if this is a localization note
      if commenttype == 'locnote':
        # parse the locnote into the entity and the actual note
        typeend = quote.findend(locnote,'LOCALIZATION NOTE')

        # parse the id
        idstart = locnote.find('(',typeend)
        if idstart == -1: continue
        idend = locnote.find(')',idstart+1)

        entity = locnote[idstart+1:idend].strip()

        # parse the actual note
        actualnotestart = locnote.find(':',idend+1)
        actualnoteend = locnote.find('-->',idend)

        actualnote = locnote[actualnotestart+1:actualnoteend].strip()

        # if it's for this entity, process it
        if thedtd.entity == entity:
          # if it says don't translate (and nothing more),
          if actualnote == "DONT_TRANSLATE":
            # take out the entity,definition and the DONT_TRANSLATE comment
            thedtd.entity = ""
            thedtd.definition = ""
            del thedtd.comments[commentnum]
            # finished this for loop
            break
          else:
            # convert it into a msgidcomment, to be processed by convertcomments
            # the actualnote is followed by a literal \n
            thedtd.comments[commentnum] = ("msgidcomment",quote.quotestr("_: "+actualnote+"\\n"))

    # do a standard translation
    self.convertcomments(thedtd,thepo)
    self.convertstrings(thedtd,thepo)

    return thepo

  def makeheader(self, filename):
    """create a header for the given filename"""
    # TODO: handle this in the po class
    headerpo = po.poelement()
    headerpo.othercomments.append("# extracted from %s\n" % filename)
    headerpo.typecomments.append("#, fuzzy\n")
    headerpo.msgid = ['""']
    headeritems = [""]
# SOME DESCRIPTIVE TITLE.
# Copyright (C) YEAR Free Software Foundation, Inc.
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
#
#, fuzzy
    headeritems.append("Project-Id-Version: PACKAGE VERSION\\n")
    headeritems.append("POT-Creation-Date: 2002-07-15 17:13+0100\\n")
    headeritems.append("PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n")
    headeritems.append("Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n")
    headeritems.append("Language-Team: LANGUAGE <LL@li.org>\\n")
    headeritems.append("MIME-Version: 1.0\\n")
    headeritems.append("Content-Type: text/plain; charset=CHARSET\\n")
    headeritems.append("Content-Transfer-Encoding: ENCODING\\n")
    headerpo.msgstr = [quote.quotestr(headerstr) for headerstr in headeritems]
    return headerpo

  def findmixedentities(self, thedtdfile):
    """creates self.mixedentities from the dtd file..."""
    self.mixedentities = {} # those entities which have a .label and .accesskey combined
    for entity in thedtdfile.index.keys():
      if entity.endswith(".label"):
        entitybase = entity[:entity.rfind(".label")]
        # see if there is a matching accesskey in this line, making this a
        # mixed entity
        if thedtdfile.index.has_key(entitybase + ".accesskey"):
          # add both versions to the list of mixed entities
          self.mixedentities[entity] = 0
          self.mixedentities[entitybase+".accesskey"] = 0
      # check if this could be a mixed entity (".label" and ".accesskey")

  def convertdtdelement(self, thedtdfile, thedtd):
    """converts a dtd element from thedtdfile to a po element, handling mixed entities along the way..."""
    # keep track of whether acceskey and label were combined
    if thedtd.entity in self.mixedentities:
      # use special convertmixed element which produces one poelement with
      # both combined for the label and None for the accesskey
      alreadymixed = self.mixedentities[thedtd.entity]
      if alreadymixed:
        # we are successfully throwing this away...
        return None
      else:
        # depending on what we come across first, work out the label and the accesskey
        if thedtd.entity.endswith(".label"):
          labelentity, labeldtd = thedtd.entity, thedtd
          accesskeyentity = labelentity[:labelentity.rfind(".label")]+".accesskey"
          accesskeydtd = thedtdfile.index[accesskeyentity]
        elif thedtd.entity.endswith(".accesskey"):
          accesskeyentity, accesskeydtd = thedtd.entity, thedtd
          labelentity = accesskeyentity[:accesskeyentity.rfind(".accesskey")]+".label"
          labeldtd = thedtdfile.index[labelentity]
        thepo = self.convertmixedelement(labeldtd, accesskeydtd)
        if thepo is not None:
          self.mixedentities[accesskeyentity] = 1
          self.mixedentities[labelentity] = 1
          return thepo
        # otherwise the mix failed. add each one separately...
    return self.convertelement(thedtd)

  def convertfile(self, thedtdfile):
    thepofile = po.pofile()
    headerpo = self.makeheader(thedtdfile.filename)
    thepofile.poelements.append(headerpo)
    thedtdfile.makeindex()
    self.findmixedentities(thedtdfile)
    # go through the dtd and convert each element
    for thedtd in thedtdfile.dtdelements:
      thepo = self.convertdtdelement(thedtdfile, thedtd)
      if thepo is not None:
        thepofile.poelements.append(thepo)
    thepofile.removeduplicates()
    return thepofile

  def mergefiles(self, origdtdfile, translateddtdfile):
    thepofile = po.pofile()
    headerpo = self.makeheader("%s, %s" % (origdtdfile.filename, translateddtdfile.filename))
    thepofile.poelements.append(headerpo)
    origdtdfile.makeindex()
    self.findmixedentities(origdtdfile)
    translateddtdfile.makeindex()
    self.findmixedentities(translateddtdfile)
    # go through the dtd files and convert each element
    for origdtd in origdtdfile.dtdelements:
      origpo = self.convertdtdelement(origdtdfile, origdtd)
      if origdtd.entity in translateddtdfile.index:
        translateddtd = translateddtdfile.index[origdtd.entity]
        translatedpo = self.convertdtdelement(translateddtdfile, translateddtd)
      else:
        translatedpo = None
      if origpo is not None:
        if translatedpo is not None:
          origpo.msgstr = translatedpo.msgid
        thepofile.poelements.append(origpo)
      elif translatedpo is not None:
        print >>sys.stderr, "error converting original dtd entity %s" % origdtd.entity
    thepofile.removeduplicates()
    return thepofile

def main(inputfile, outputfile, templatefile):
  """reads in inputfile and templatefile using dtd, converts using dtd2po, writes to outputfile"""
  inputdtd = dtd.dtdfile(inputfile)
  convertor = dtd2po()
  if templatefile is None:
    outputpo = convertor.convertfile(inputdtd)
  else:
    templatedtd = dtd.dtdfile(templatefile)
    outputpo = convertor.mergefiles(templatedtd, inputdtd)
  outputpolines = outputpo.tolines()
  outputfile.writelines(outputpolines)

if __name__ == '__main__':
  # handle command line options
  from translate.convert import convert
  inputformat = "dtd"
  outputformat = "po"
  parser = convert.ConvertOptionParserExt(convert.norecursion, inputformat, outputformat, usetemplates=True)
  (options, args) = parser.parse_args()
  # open the appropriate files
  if options.input is None:
    inputfile = sys.stdin
  else:
    inputfile = open(options.input, 'r')
  if options.output is None:
    outputfile = sys.stdout
  else:
    outputfile = open(options.output, 'w')
  if options.template is None:
    templatefile = None
  else:
    templatefile = open(options.template, 'r')
  main(inputfile, outputfile, templatefile)

