#!/usr/bin/env python

"""manages projects and subprojects"""

from translate.storage import po

class TranslationIterator:
  def __init__(self, project, subproject):
    inputfile = open(subproject.pofile, "r")
    self.pofile = po.pofile(inputfile)
    self.translations = [(po.getunquotedstr(thepo.msgid), po.getunquotedstr(thepo.msgstr)) for thepo in self.pofile.poelements if not thepo.isheader()]
    self.item = 0

  def gettranslations(self, contextbefore=3, contextafter=3):
    """returns (a set of translations before, the next translation, a set of translations after)"""
    return self.translations[max(self.item-contextbefore,0):self.item], self.translations[self.item], self.translations[self.item+1:self.item+1+contextafter]

  def receivetranslation(self, item, trans):
    self.translations[item] = (self.translations[item][0], trans)
    self.item = item + 1

translationiterators = {}

def getiterator(project, subproject):
  if (self.project, self.subproject) not in translationiterators:
    translationiterators[self.project, self.subproject] = TranslationIterator(self.project, self.subproject)
  return translationiterators[self.project, self.subproject]
  
