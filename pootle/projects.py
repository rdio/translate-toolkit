#!/usr/bin/env python

"""manages projects and files and translations"""

from translate.storage import po
from translate.misc import quote
from translate.filters import checks
from translate.convert import po2csv
import os

class TranslationSession:
  """A translation session represents a users work on a particular translation project"""
  def __init__(self, project, session):
    self.session = session
    self.project = project
    self.pofilename = None
    self.lastitem = None

  def getnextitem(self, dirfilter=None, matchnames=[]):
    """gives the user the next item to be translated"""
    self.pofilename, item = self.project.searchpoitems(self.pofilename, self.lastitem, matchnames, dirfilter).next()
    return self.pofilename, item

  def receivetranslation(self, pofilename, item, trans):
    """submits a new/changed translation from the user"""
    self.project.receivetranslation(pofilename, item, trans)
    self.pofilename = pofilename
    self.lastitem = item

  def skiptranslation(self, pofilename, item):
    """skips a declined translation from the user"""
    self.pofilename = pofilename
    self.lastitem = item

class TranslationProject:
  """Manages iterating through the translations in a particular project"""
  def __init__(self, languagecode, projectcode, potree):
    self.languagecode = languagecode
    self.projectcode = projectcode
    self.potree = potree
    self.languagename = self.potree.getlanguagename(self.languagecode)
    self.projectname = self.potree.getprojectname(self.languagecode, self.projectcode)
    self.podir = potree.getpodir(languagecode, projectcode)
    self.checker = checks.StandardChecker()
    self.pofilenames = []
    self.pofiles = {}
    self.stats = {}
    os.path.walk(self.podir, self.addfiles, None)
    self.initstatscache()

  def browsefiles(self, dirfilter=None, depth=None, maxdepth=None, includedirs=False, includefiles=True):
    """gets a list of pofilenames, optionally filtering with the parent directory"""
    if dirfilter is None:
      pofilenames = self.pofilenames
    else:
      if not dirfilter.endswith(os.path.sep) and not dirfilter.endswith(os.path.extsep + "po"):
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

  def iterpofilenames(self, lastpofilename=None, includelast=False):
    """iterates through the pofilenames starting after the given pofilename"""
    if lastpofilename is None:
      index = 0
    else:
      index = self.pofilenames.index(lastpofilename)
      if not includelast:
        index += 1
    while index < len(self.pofilenames):
      yield self.pofilenames[index]
      index += 1

  def searchpofilenames(self, lastpofilename, matchnames, dirfilter, includelast=False):
    """find the next pofilename that has items matching one of the given classification names"""
    for pofilename in self.iterpofilenames(lastpofilename, includelast):
      if dirfilter is not None and not pofilename.startswith(dirfilter):
        continue
      if not matchnames:
        yield pofilename
      postats = self.getpostats(pofilename)
      for name in matchnames:
        if postats[name]:
          yield pofilename

  def iterpoitems(self, pofile, lastitem=None, matchnames=None):
    """iterates through the items in the given pofile starting after the given lastitem"""
    if lastitem is None:
      item = 0
    else:
      item = lastitem + 1
    while item < len(pofile.transelements):
      if not matchnames:
        yield item
      for name in matchnames:
        if item in pofile.classify[name]:
          yield item
      item += 1

  def searchpoitems(self, pofilename, item, matchnames, dirfilter):
    """finds the next item matching one of the given classification names"""
    for pofilename in self.searchpofilenames(pofilename, matchnames, dirfilter, includelast=True):
      pofile = self.getpofile(pofilename)
      for item in self.iterpoitems(pofile, item, matchnames):
        yield pofilename, item

  def gettranslationsession(self, session):
    """gets the user's translationsession"""
    if not hasattr(session, "translationsessions"):
      session.translationsessions = {}
    if not (self.languagecode, self.projectcode) in session.translationsessions:
      session.translationsessions[self.languagecode, self.projectcode] = TranslationSession(self, session)
    return session.translationsessions[self.languagecode, self.projectcode]

  def initstatscache(self):
    """reads cached statistics from the disk"""
    for pofilename in self.pofilenames:
      if not pofilename in self.stats:
        abspofilename = os.path.join(self.podir, pofilename)
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
    # print "creating stats for",pofilename
    pofile = self.getpofile(pofilename)
    postats = dict([(name, len(items)) for name, items in pofile.classify.iteritems()])
    self.stats[pofilename] = postats
    abspofilename = os.path.join(self.podir, pofilename)
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
    basedirname = dirname.replace(self.podir, "")
    while basedirname.startswith(os.sep):
      basedirname = basedirname.replace(os.sep, "", 1)
    ponames = [fname for fname in fnames if fname.endswith(os.extsep+"po")]
    self.pofilenames.extend([os.path.join(basedirname, poname) for poname in ponames])

  def getpofile(self, pofilename):
    """parses the file into a pofile object and stores in self.pofiles"""
    if pofilename in self.pofiles:
      return self.pofiles[pofilename]
    abspofilename = os.path.join(self.podir, pofilename)
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
      pofile.classify["check-" + checkname] = []
    for item, poel in enumerate(pofile.transelements):
      unquotedid = po.getunquotedstr(poel.msgid, joinwithlinebreak=False)
      unquotedstr = po.getunquotedstr(poel.msgstr, joinwithlinebreak=False)
      failures = self.checker.run_filters(unquotedid, unquotedstr)
      for failure in failures:
        functionname = failure.split(":",2)[0]
        pofile.classify["check-" + functionname].append(item)
    self.pofiles[pofilename] = pofile
    return pofile

  def getpofilelen(self, pofilename):
    """returns number of items in the given pofilename"""
    pofile = self.getpofile(pofilename)
    return len(pofile.transelements)

  def getitem(self, pofilename, item):
    """returns a particular item from a particular po file's orig, trans strings as a tuple"""
    pofile = self.project.getpofile(pofilename)
    thepo = pofile.transelements[item]
    orig, trans = po.getunquotedstr(thepo.msgid), po.getunquotedstr(thepo.msgstr)
    return orig, trans

  def getitems(self, pofilename, itemstart, itemstop):
    """returns num items before the given item, as context"""
    pofile = self.getpofile(pofilename)
    elements = pofile.transelements[max(itemstart,0):itemstop]
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
    abspofilename = os.path.join(self.podir, pofilename)
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

class POTree:
  """Manages the tree of projects and languages"""
  def __init__(self, instance):
    self.languages = instance.languages
    self.projects = {}

  def haslanguage(self, languagecode):
    """checks if this language exists"""
    return hasattr(self.languages, languagecode)

  def getlanguageprefs(self, languagecode):
    """returns the language object"""
    return getattr(self.languages, languagecode)

  def getlanguagename(self, languagecode):
    """returns the language's full name"""
    return getattr(self.getlanguageprefs(languagecode), "fullname", languagecode)

  def getlanguagecodes(self):
    """returns a list of valid languagecodes"""
    return [languagecode for languagecode, language in self.languages.iteritems()]

  def getprojectcodes(self, languagecode):
    """returns a list of project codes that are valid for the given languagecode"""
    languageprefs = self.getlanguageprefs(languagecode)
    return [projectcode for projectcode, projectprefs in languageprefs.projects.iteritems()]

  def hasproject(self, languagecode, projectcode):
    """returns whether the project exists for the language"""
    if not self.haslanguage(languagecode):
      return False
    languageprefs = self.getlanguageprefs(languagecode)
    return hasattr(languageprefs.projects, projectcode)

  def getproject(self, languagecode, projectcode):
    """returns the project object for the languagecode and projectcode"""
    if (languagecode, projectcode) not in self.projects:
      self.projects[languagecode, projectcode] = TranslationProject(languagecode, projectcode, self)
    return self.projects[languagecode, projectcode]

  def getprojectname(self, languagecode, projectcode):
    """returns the full name of the project"""
    languageprefs = self.getlanguageprefs(languagecode)
    projectprefs = getattr(languageprefs.projects, projectcode)
    return getattr(projectprefs, "fullname", projectcode)

  def getpodir(self, languagecode, projectcode):
    """returns the full name of the project"""
    languageprefs = self.getlanguageprefs(languagecode)
    projectprefs = getattr(languageprefs.projects, projectcode)
    return projectprefs.podir


