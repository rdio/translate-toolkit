#!/usr/bin/env python

"""manages projects and files and translations"""

from translate.storage import po
from translate.misc import quote
from translate.filters import checks
# TODO: po2csv needs to be made an importable module
# from translate.convert import po2csv
import os

class TranslationSession:
  """A translation session represents a users work on a particular translation project"""
  def __init__(self, translationproject, session):
    self.session = session
    self.translationproject = translationproject
    self.pofilename = None
    self.pofile = None
    self.lastitem = None

  def getnextitem(self, dirfilter=None):
    """gives the user the next item to be translated"""
    matchnames = ["fuzzy", "blank"]
    self.pofilename, item = self.translationproject.findnextitem(self.pofilename, self.lastitem, matchnames, dirfilter)
    self.pofile = self.translationproject.getpofile(self.pofilename)
    thepo = self.pofile.transelements[item]
    orig, trans = po.getunquotedstr(thepo.msgid), po.getunquotedstr(thepo.msgstr)
    return self.pofilename, item, orig, trans

  def receivetranslation(self, pofilename, item, trans):
    """submits a new/changed translation from the user"""
    self.translationproject.receivetranslation(pofilename, item, trans)
    self.pofilename = pofilename
    self.lastitem = item

  def skiptranslation(self, pofilename, item):
    """skips a declined translation from the user"""
    self.pofilename = pofilename
    self.lastitem = item

class TranslationProject:
  """Manages iterating through the translations in a particular project"""
  def __init__(self, project):
    self.project = project
    self.checker = checks.StandardChecker()
    self.pofilenames = []
    self.pofiles = {}
    self.stats = {}
    os.path.walk(self.project.podir, self.addfiles, None)
    self.initstatscache()

  def browsefiles(self, dirfilter=None, depth=None, maxdepth=None, includedirs=False, includefiles=True):
    """gets a list of pofilenames, optionally filtering with the parent directory"""
    if dirfilter is None:
      pofilenames = self.pofilenames
    else:
      if not dirfilter.endswith(os.path.sep):
        dirfilter += os.path.sep
      pofilenames = [pofilename for pofilename in self.pofilenames if pofilename.startswith(dirfilter)]
    if includedirs:
      podirs = {}
      for pofilename in pofilenames:
        dirname = os.path.dirname(pofilename)
	if not dirname:
	  continue
        podirs[dirname] = True
	while dirname:
	  dirname = os.path.dirname(dirname)
	  if dirname:
	    podirs[dirname] = True
      podirs = podirs.keys()
    else:
      podirs = []
    if not includefiles:
      pofilenames = []
    if maxdepth is not None:
      pofilenames = [pofilename for pofilename in pofilenames if pofilename.count(os.path.sep) <= maxdepth]
      podirs = [podir for podir in podirs if podir.count(os.path.sep) <= maxdepth]
    if depth is not None:
      pofilenames = [pofilename for pofilename in pofilenames if pofilename.count(os.path.sep) == depth]
      podirs = [podir for podir in podirs if podir.count(os.path.sep) == depth]
    return pofilenames + podirs

  def getnextpofilename(self, pofilename):
    """gets the pofilename that comes after the given one (or the first if pofilename is None)"""
    if pofilename is None:
      return self.pofilenames[0]
    else:
      index = self.pofilenames.index(pofilename)
      return self.pofilenames[index+1]

  def findnextpofilename(self, pofilename, matchnames, dirfilter):
    """find the next pofilename that has items matching one of the given classification names"""
    matches = False
    while not matches:
      pofilename = self.getnextpofilename(pofilename)
      if dirfilter is not None and not pofilename.startswith(dirfilter):
        continue
      if matchnames is None:
        return pofilename
      postats = self.getpostats(pofilename)
      for name in matchnames:
        if postats[name]:
          return pofilename
    raise IndexError("no more pofilenames could be found")

  def findnextitem(self, pofilename, item, matchnames, dirfilter):
    """finds the next item matching one of the given classification names"""
    matches = False
    while not matches:
      pofilename, item = self.getnextitem(pofilename, item, matchnames, dirfilter)
      pofile = self.getpofile(pofilename)
      matches = False
      for name in matchnames:
        if item in pofile.classify[name]:
          matches = True
          continue
    return pofilename, item

  def getnextitem(self, pofilename, lastitem, matchnames, dirfilter):
    """skips to the next item. uses matchnames to filter next pofile if required"""
    if lastitem is None:
      item = 0
    else:
      item = lastitem + 1
    if pofilename is None:
      pofile = None
    else:
      pofile = self.getpofile(pofilename)
    while pofile is None or item >= len(pofile.transelements):
      if matchnames:
        pofilename = self.findnextpofilename(pofilename, matchnames, dirfilter)
      else:
        pofilename = self.findnextpofilename(pofilename, None, dirfilter)
      pofile = self.getpofile(pofilename)
      item = 0
    return pofilename, item

  def gettranslationsession(self, session):
    """gets the user's translationsession"""
    if not hasattr(session, "translationsessions"):
      session.translationsessions = {}
    if not self.project in session.translationsessions:
      session.translationsessions[self.project] = TranslationSession(self, session)
    return session.translationsessions[self.project]

  def initstatscache(self):
    """reads cached statistics from the disk"""
    for pofilename in self.pofilenames:
      if not pofilename in self.stats:
        abspofilename = os.path.join(self.project.podir, pofilename)
        pomtime = os.stat(abspofilename)[os.path.stat.ST_MTIME]
        statsfilename = abspofilename + os.extsep + "stats"
        if os.path.exists(statsfilename):
          try:
            stats = open(statsfilename, "r").read()
            statsmtime, postatsstring = stats.split("\n", 1)
            statsmtime = int(statsmtime)
            postats = {}
            for line in postatsstring.split("\n"):
              name, count = line.split(":", 1)
              count = int(count.strip())
              postats[name.strip()] = count
          except:
            # TODO: provide some logging here for debugging...
            continue
          if pomtime != statsmtime:
            continue
          self.stats[pofilename] = postats

  def calculatestats(self, pofilenames=None):
    """calculates translation statistics for the given po files (or all if None given)"""
    totalstats = {}
    if pofilenames is None:
      pofilenames = self.pofilenames
    for pofilename in pofilenames:
      if not pofilename or os.path.isdir(pofilename):
        continue
      postats = self.getpostats(pofilename)
      for name, count in postats.iteritems():
        totalstats[name] = totalstats.get(name, 0) + count
    return totalstats

  def getpostats(self, pofilename):
    """calculates translation statistics for the given po file"""
    if pofilename in self.stats:
      return self.stats[pofilename]
    pofile = self.getpofile(pofilename)
    postats = dict([(name, len(items)) for name, items in pofile.classify.iteritems()])
    self.stats[pofilename] = postats
    abspofilename = os.path.join(self.project.podir, pofilename)
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
    basedirname = dirname.replace(self.project.podir, "")
    while basedirname.startswith(os.sep):
      basedirname = basedirname.replace(os.sep, "", 1)
    ponames = [fname for fname in fnames if fname.endswith(os.extsep+"po")]
    self.pofilenames.extend([os.path.join(basedirname, poname) for poname in ponames])

  def getpofile(self, pofilename):
    """parses the file into a pofile object and stores in self.pofiles"""
    if pofilename in self.pofiles:
      return self.pofiles[pofilename]
    abspofilename = os.path.join(self.project.podir, pofilename)
    inputfile = open(abspofilename, "r")
    pofile = po.pofile(inputfile)
    # we ignore all the headers by using this filtered set
    pofile.transelements = [poel for poel in pofile.poelements if not (poel.isheader() or poel.isblank())]
    # we always want to have the classifications available
    pofile.classify = {}
    pofile.classify["fuzzy"] = [item for item, poel in enumerate(pofile.transelements) if poel.isfuzzy()]
    pofile.classify["blank"] = [item for item, poel in enumerate(pofile.transelements) if poel.isblankmsgstr()]
    pofile.classify["translated"] = [item for item, poel in enumerate(pofile.transelements) if item not in pofile.classify["fuzzy"] and item not in pofile.classify["blank"]]
    pofile.classify["total"] = range(len(pofile.transelements))
    for checkname in self.checker.getfilters().keys():
      pofile.classify[checkname] = []
    for item, poel in enumerate(pofile.transelements):
      unquotedid = po.getunquotedstr(poel.msgid, joinwithlinebreak=False)
      unquotedstr = po.getunquotedstr(poel.msgstr, joinwithlinebreak=False)
      failures = self.checker.run_filters(unquotedid, unquotedstr)
      for failure in failures:
        functionname = failure.split(":",2)[0]
        pofile.classify["check-" + functionname].append(item)
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
    abspofilename = os.path.join(self.project.podir, pofilename)
    open(abspofilename, "w").writelines(lines)

  def getsource(self, pofilename):
    """returns pofile source"""
    pofile = self.getpofile(pofilename)
    lines = pofile.tolines()
    return "".join(lines)

  def getcsv(self, csvfilename):
    """returns pofile as csv"""
    pofilename = csvfilename.replace(".csv", ".po")
    pofile = self.getpofile(pofilename)
    convertor = po2csv.po2csv()
    csvfile = convertor.convertfile(pofile)
    lines = csvfile.tolines()
    return "".join(lines)

projects = {}

def getproject(project):
  if project not in projects:
    projects[project] = TranslationProject(project)
  return projects[project]
  
