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
    matchtest = lambda thepo: thepo.isfuzzy() or thepo.isblankmsgstr()
    self.pofilename, item = self.translationproject.findnextitem(self.pofilename, self.lastitem, matchtest)
    self.pofile = self.translationproject.getpofile(self.pofilename)
    thepo = self.pofile.transelements[item]
    orig, trans = po.getunquotedstr(thepo.msgid), po.getunquotedstr(thepo.msgstr)
    return self.pofilename, item, orig, trans

  def receivetranslation(self, pofilename, item, trans):
    """submits a new/changed translation from the user"""
    self.translationproject.receivetranslation(pofilename, item, trans)
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

  def findnextitem(self, pofilename, item, matchtest):
    """finds the next item matching the given filter criteria"""
    matches = False
    while not matches:
      pofilename, item = self.getnextitem(pofilename, item)
      pofile = self.getpofile(pofilename)
      thepo = pofile.transelements[item]
      matches = matchtest(thepo)
    return pofilename, item

  def getnextitem(self, pofilename, lastitem):
    """skips to the next item"""
    if lastitem is None:
      item = 0
    else:
      item = lastitem + 1
    if pofilename is None:
      pofile = None
    else:
      pofile = self.getpofile(pofilename)
    while pofile is None or item >= len(pofile.transelements):
      pofilename = self.getnextpofilename(pofilename)
      pofile = self.getpofile(pofilename)
      item = 0
    return pofilename, item

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
        abspofilename = os.path.join(self.subproject.podir, pofilename)
        pomtime = os.stat(abspofilename)[os.path.stat.ST_MTIME]
        statsfilename = abspofilename + os.extsep + "stats"
        if os.path.exists(statsfilename):
          try:
            stats = open(statsfilename, "r").read()
            statsmtime, postatsstring = stats.split("\n", 1)
            postats = {}
            for line in postatsstring.split("\n"):
              name, count = line.split(":", 1)
              count = int(count.strip())
              postats[name.strip()] = count
          except:
            continue
          if pomtime != statsmtime:
            continue
          self.stats[pofilename] = postats

  def calculatestats(self):
    """calculates translation statistics for all the po files"""
    totalstats = {}
    for pofilename in self.pofilenames:
      postats = self.getpostats(pofilename)
      for name, count in postats.iteritems():
        totalstats[name] = totalstats.get(name, 0) + count
    return totalstats

  def getpostats(self, pofilename):
    """calculates translation statistics for the given po file"""
    if pofilename in self.stats:
      return self.stats[pofilename]
    pofile = self.getpofile(pofilename)
    pofile.classify = {}
    pofile.classify["fuzzy"] = [item for item, poel in enumerate(pofile.transelements) if poel.isfuzzy()]
    pofile.classify["blank"] = [item for item, poel in enumerate(pofile.transelements) if poel.isblankmsgstr()]
    pofile.classify["translated"] = [item for item, poel in enumerate(pofile.transelements) if item not in pofile.classify["fuzzy"] and item not in pofile.classify["blank"]]
    pofile.classify["total"] = range(len(pofile.transelements))
    postats = dict([(name, len(items)) for name, items in pofile.classify.iteritems()])
    self.stats[pofilename] = postats
    abspofilename = os.path.join(self.subproject.podir, pofilename)
    pomtime = os.stat(abspofilename)[os.path.stat.ST_MTIME]
    statsfilename = abspofilename + os.extsep + "stats"
    try:
      postatsstring = "\n".join(["%s:%d" % (name, count) for name, count in postats.iteritems()])
      open(statsfilename, "w").write("%d\n%s" % (pomtime, postatsstring))
    except IOError:
      pass
    return self.stats[pofilename]

  def addfiles(self, dummy, dirname, fnames):
    """adds the files to the set of files for this project"""
    basedirname = dirname.replace(self.subproject.podir, "")
    while basedirname.startswith(os.sep):
      basedirname = basedirname.replace(os.sep, "", 1)
    ponames = [fname for fname in fnames if fname.endswith(os.extsep+"po")]
    self.pofilenames.extend([os.path.join(basedirname, poname) for poname in ponames])

  def getpofile(self, pofilename):
    """parses the file into a pofile object and stores in self.pofiles"""
    if pofilename in self.pofiles:
      return self.pofiles[pofilename]
    abspofilename = os.path.join(self.subproject.podir, pofilename)
    inputfile = open(abspofilename, "r")
    pofile = po.pofile(inputfile)
    # we ignore all the headers by using this filtered set
    pofile.transelements = [poel for poel in pofile.poelements if not (poel.isheader() or poel.isblank())]
    self.pofiles[pofilename] = pofile
    return pofile

  def getitemsbefore(self, pofilename, item, num=3):
    """returns num items before the given item, as context"""
    pofile = self.getpofile(pofilename)
    elements = pofile.transelements[max(item-num,0):item]
    return [(po.getunquotedstr(poel.msgid), po.getunquotedstr(poel.msgstr)) for poel in elements]

  def getitemsafter(self, pofilename, item, num=3):
    """returns num items after the given item, as context"""
    pofile = self.getpofile(pofilename)
    elements = pofile.transelements[item+1:item+1+num]
    return [(po.getunquotedstr(poel.msgid), po.getunquotedstr(poel.msgstr)) for poel in elements]

  def receivetranslation(self, pofilename, item, trans):
    """receives a new translation that has been submitted..."""
    pofile = self.getpofile(pofilename)
    pofile.transelements[item].msgstr = [quote.quotestr(transpart) for transpart in trans.split("\n")]
    del self.stats[pofilename]
    self.savefile(pofilename)

  def savefile(self, pofilename):
    """saves changes to disk..."""
    pofile = self.getpofile(pofilename)
    lines = pofile.tolines()
    abspofilename = os.path.join(self.subproject.podir, pofilename)
    open(abspofilename, "w").writelines(lines)

projects = {}

def getproject(subproject):
  if subproject not in projects:
    projects[subproject] = TranslationProject(subproject)
  return projects[subproject]
  
