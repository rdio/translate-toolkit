#!/usr/bin/env python

"""manages projects and subprojects"""

from translate.storage import po
import os

class TranslationIterator:
  """Manages iterating through the translations in a project"""
  def __init__(self, project, subproject):
    self.pofilenames = []
    self.pofiles = {}
    os.path.walk(subproject.podir, self.addfiles, None)
    self.currentpofile = None
    self.fileindex = None
    self.item = 0
    self.translations = []

  def addfiles(self, dummy, dirname, fnames):
    """adds the files to the set of files for this project"""
    ponames = [fname for fname in fnames if fname.endswith(os.extsep+"po")]
    self.pofilenames.extend([os.path.join(dirname, poname) for poname in ponames])

  def parsefile(self, pofilename):
    """parses the file into a pofile object and stores in self.pofiles"""
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
    self.currentpofile = self.parsefile(pofilename)
    self.item = 0
    self.translations = [(po.getunquotedstr(thepo.msgid), po.getunquotedstr(thepo.msgstr)) for thepo in self.currentpofile.poelements if not thepo.isheader()]

  def gettranslations(self, contextbefore=3, contextafter=3):
    """returns (a set of translations before, the next translation, a set of translations after)"""
    if self.currentpofile is None or self.item >= len(self.translations):
      self.getnextpofile()
    return self.translations[max(self.item-contextbefore,0):self.item], self.translations[self.item], self.translations[self.item+1:self.item+1+contextafter]

  def receivetranslation(self, item, trans):
    self.translations[item] = (self.translations[item][0], trans)
    self.item = item + 1

translationiterators = {}

def getiterator(project, subproject):
  if (project, subproject) not in translationiterators:
    translationiterators[project, subproject] = TranslationIterator(project, subproject)
  return translationiterators[project, subproject]
  
