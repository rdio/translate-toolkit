#!/usr/bin/env python

"""manages projects and subprojects"""

from translate.storage import po
from translate.misc import quote
import os

class TranslationSession:
  """A translation session represents a users work on a particular translation project"""
  def __init__(self, translationproject, session):
    self.session = session
    self.translationproject = translationproject
    self.pofilename = None
    self.pofile = None
    self.lastitem = None

  def getnextitem(self):
    """gives the user the next item to be translated"""
    if self.lastitem is None:
      item = 0
    else:
      item = self.lastitem + 1
    while self.pofile is None or item >= len(self.pofile.transelements):
      self.pofilename = self.translationproject.getnextpofilename(self.pofilename)
      self.pofile = self.translationproject.getpofile(self.pofilename)
      item = 0
    thepo = self.pofile.transelements[item]
    orig, trans = po.getunquotedstr(thepo.msgid), po.getunquotedstr(thepo.msgstr)
    return self.pofilename, item, orig, trans

  def receivetranslation(self, pofilename, item, trans):
    """submits a new/changed translation from the user"""
    pofile = self.translationproject.getpofile(pofilename)
    pofile.transelements[item].msgstr = [quote.quotestr(transpart) for transpart in trans.split("\n")]
    if pofilename == self.pofilename:
      self.lastitem = item

class TranslationProject:
  """Manages iterating through the translations in a particular project"""
  def __init__(self, subproject):
    self.subproject = subproject
    self.pofilenames = []
    self.pofiles = {}
    self.stats = {}
    os.path.walk(self.subproject.podir, self.addfiles, None)
    self.initstatscache()
    for pofilename in self.pofiles:
      self.getpofile(pofilename)

  def getnextpofilename(self, pofilename):
    """gets the pofilename that comes after the given one (or the first if pofilename is None)"""
    if pofilename is None:
      return self.pofilenames[0]
    else:
      index = self.pofilenames.index(pofilename)
      return self.pofilenames[index+1]

  def gettranslationsession(self, session):
    """gets the user's translationsession"""
    if not hasattr(session, "translationsessions"):
      session.translationsessions = {}
    if not self.subproject in session.translationsessions:
      session.translationsessions[self.subproject] = TranslationSession(self, session)
    return session.translationsessions[self.subproject]

  def initstatscache(self):
    """reads cached statistics from the disk"""
    for pofilename in self.pofilenames:
      if not pofilename in self.stats:
        pomtime = os.stat(pofilename)[os.path.stat.ST_MTIME]
        statsfilename = pofilename + os.extsep + "stats"
        if os.path.exists(statsfilename):
          try:
            stats = open(statsfilename, "r").read()
            statsmtime, translated, total = [int(n) for n in stats.split()[:3]]
          except:
            continue
          if pomtime != statsmtime:
            continue
          self.stats[pofilename] = (translated, total)

  def calculatestats(self):
    """calculates translation statistics for all the po files"""
    translated, total = 0, 0
    for pofilename in self.pofilenames:
      potranslated, pototal = self.getpostats(pofilename)
      translated += potranslated
      total += pototal
    return translated, total

  def getpostats(self, pofilename):
    """calculates translation statistics for the given po file"""
    if pofilename in self.stats:
      return self.stats[pofilename]
    pofile = self.getpofile(pofilename)
    translated = len(filter(lambda poel: po.getunquotedstr(poel.msgstr).strip() and not poel.isfuzzy(), pofile.transelements))
    total = len(pofile.transelements)
    self.stats[pofilename] = (translated, total)
    pomtime = os.stat(pofilename)[os.path.stat.ST_MTIME]
    statsfilename = pofilename + os.extsep + "stats"
    try:
      open(statsfilename, "w").write("%d %d %d" % (pomtime, translated, total))
    except:
      pass
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
    # we ignore all the headers by using this filtered set
    pofile.transelements = [poel for poel in pofile.poelements if not (poel.isheader() or poel.isblank())]
    self.pofiles[pofilename] = pofile
    return pofile

  def getitemsbefore(self, pofilename, item, num=3):
    pofile = self.getpofile(pofilename)
    elements = pofile.transelements[max(item-num,0):item]
    return [(po.getunquotedstr(poel.msgid), po.getunquotedstr(poel.msgstr)) for poel in elements]

  def getitemsafter(self, pofilename, item, num=3):
    pofile = self.getpofile(pofilename)
    elements = pofile.transelements[item+1:item+1+num]
    return [(po.getunquotedstr(poel.msgid), po.getunquotedstr(poel.msgstr)) for poel in elements]

projects = {}

def getproject(subproject):
  if subproject not in projects:
    projects[subproject] = TranslationProject(subproject)
  return projects[subproject]
  
