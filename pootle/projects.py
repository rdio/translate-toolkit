#!/usr/bin/env python

"""manages projects and subprojects"""

from translate.storage import po
import os

class TranslationProject:
  """Manages iterating through the translations in a particular project"""
  def __init__(self, project, subproject):
    self.pofilenames = []
    self.pofiles = {}
    self.stats = {}
    os.path.walk(subproject.podir, self.addfiles, None)
    for pofilename in self.pofiles:
      self.getpofile(pofilename)
    self.currentpofile = None
    self.fileindex = None
    self.item = 0
    self.translations = []

  def calculatestats(self):
    translated, total = 0, 0
    for pofilename in self.pofilenames:
      potranslated, pototal = self.getpostats(pofilename)
      translated += potranslated
      total += pototal
    return translated, total

  def getpostats(self, pofilename):
    if pofilename in self.stats:
      return self.stats[pofilename]
    pofile = self.getpofile(pofilename)
    elements = filter(lambda poel: not (poel.isblank() or poel.isheader()), pofile.poelements)
    translated = len(filter(lambda poel: po.getunquotedstr(poel.msgstr).strip() and not poel.isfuzzy(), elements))
    total = len(elements)
    self.stats[pofilename] = (translated, total)
    return self.stats[pofilename]

  def addfiles(self, dummy, dirname, fnames):
    """adds the files to the set of files for this project"""
    ponames = [fname for fname in fnames if fname.endswith(os.extsep+"po")]
    self.pofilenames.extend([os.path.join(dirname, poname) for poname in ponames])

  def getpofile(self, pofilename):
    """parses the file into a pofile object and stores in self.pofiles"""
    if pofilename in self.pofiles:
      return self.pofiles[pofilename]
    inputfile = open(pofilename, "r")
    pofile = po.pofile(inputfile)
    self.pofiles[pofilename] = pofile
    return pofile

  def getnextpofile(self):
    """sets self.currentpofile to the next po file in order"""
    if self.fileindex is None:
      self.fileindex = 0
    else:
      self.fileindex += 1
    pofilename = self.pofilenames[self.fileindex]
    self.currentpofile = self.getpofile(pofilename)
    self.item = 0
    self.translations = [(po.getunquotedstr(thepo.msgid), po.getunquotedstr(thepo.msgstr)) for thepo in self.currentpofile.poelements if not thepo.isheader()]

  def gettranslations(self, contextbefore=3, contextafter=3):
    """returns (a set of translations before, the next translation, a set of translations after)"""
    if self.currentpofile is None or self.item >= len(self.translations):
      self.getnextpofile()
    return self.translations[max(self.item-contextbefore,0):self.item], self.translations[self.item], self.translations[self.item+1:self.item+1+contextafter]

  def receivetranslation(self, item, trans):
    # TODO: this needs to be given the filename as well, otherwise its meaningless...
    self.translations[item] = (self.translations[item][0], trans)
    self.item = item + 1

projects = {}

def getproject(project, subproject):
  if (project, subproject) not in projects:
    projects[project, subproject] = TranslationProject(project, subproject)
  return projects[project, subproject]
  
