#!/usr/bin/env python

"""manages projects and files and translations"""

from translate.storage import po
from translate.misc import quote
from translate.filters import checks
from translate.filters import pofilter
from translate.convert import po2csv
from translate.convert import pot2po
from translate.tools import pocompile
from translate.tools import pogrep
from jToolkit import timecache
import time
import os
import sre
import cStringIO
try:
  import PyLucene
except:
  PyLucene = None

def getmodtime(filename, default=None):
  """gets the modificationtime of the given file"""
  if os.path.exists(filename):
    return os.stat(filename)[os.path.stat.ST_MTIME]
  else:
    return default

class RightsError(ValueError):
  pass

languagere = sre.compile("^[a-z]{2,3}([_-][A-Z]{2,3}|)$")
regionre = sre.compile("^[_-][A-Z]{2,3}$")

class TranslationSession:
  """A translation session represents a users work on a particular translation project"""
  def __init__(self, project, session):
    self.session = session
    self.project = project
    self.rights = self.getrights()

  def getrights(self):
    """gets the current users rights"""
    if self.session.isopen:
      return ["view", "review", "translate"]
    else:
      return ["view"]

  def receivetranslation(self, pofilename, item, trans, issuggestion):
    """submits a new/changed translation from the user"""
    if self.session.isopen:
      username = self.session.username
    else:
      username = None
    if issuggestion:
      if "suggest" not in self.rights:
        raise RightsError(self.session.localize("you do not have rights to suggest changes here"))
      self.project.suggesttranslation(pofilename, item, trans, username)
    else:
      if "translate" not in self.rights:
        raise RightsError(self.session.localize("you do not have rights to change translations here"))
      self.project.updatetranslation(pofilename, item, trans, username)

  def skiptranslation(self, pofilename, item):
    """skips a declined translation from the user"""
    pass

class pootlefile(po.pofile):
  """this represents a pootle-managed .po file and its associated files"""
  def __init__(self, project, pofilename):
    po.pofile.__init__(self)
    self.project = project
    self.checker = self.project.checker
    self.pofilename = pofilename
    self.filename = os.path.join(self.project.podir, self.pofilename)
    self.statsfilename = self.filename + os.extsep + "stats"
    self.pendingfilename = self.filename + os.extsep + "pending"
    self.assignsfilename = self.filename + os.extsep + "assigns"
    self.pendingfile = None
    # we delay parsing until it is required
    self.pomtime = None
    self.getstats()
    self.getassigns()
    self.tracker = timecache.timecache(20*60)

  def track(self, item, message):
    """sets the tracker message for the given item"""
    self.tracker[item] = message
    print message

  def readpofile(self):
    """reads and parses the main po file"""
    self.poelements = []
    pomtime = getmodtime(self.filename)
    self.parse(open(self.filename, 'r'))
    # we ignore all the headers by using this filtered set
    self.transelements = [poel for poel in self.poelements if not (poel.isheader() or poel.isblank())]
    self.classifyelements()
    self.pomtime = pomtime

  def savepofile(self):
    """saves changes to the main file to disk..."""
    lines = self.tolines()
    open(self.filename, "w").writelines(lines)
    # don't need to reread what we saved
    self.pomtime = getmodtime(self.filename)

  def pofreshen(self):
    """makes sure we have a freshly parsed pofile"""
    if self.pomtime != getmodtime(self.filename):
      self.readpofile()

  def getsource(self):
    """returns pofile source"""
    self.pofreshen()
    lines = self.tolines()
    return "".join(lines)

  def getcsv(self):
    """returns pofile as csv"""
    self.pofreshen()
    convertor = po2csv.po2csv()
    csvfile = convertor.convertfile(self)
    lines = csvfile.tolines()
    return "".join(lines)

  def getmo(self):
    """returns pofile compiled into mo"""
    self.pofreshen()
    convertor = pocompile.pocompile()
    mofile = convertor.convertfile(self)
    return mofile

  def readpendingfile(self):
    """reads and parses the pending file corresponding to this po file"""
    if os.path.exists(self.pendingfilename):
      pendingmtime = getmodtime(self.pendingfilename)
      if pendingmtime == getattr(self, "pendingmtime", None):
        return
      inputfile = open(self.pendingfilename, "r")
      self.pendingmtime, self.pendingfile = pendingmtime, po.pofile(inputfile)
      if self.pomtime:
        self.reclassifysuggestions()
    else:
      self.pendingfile = po.pofile()
      self.savependingfile()

  def savependingfile(self):
    """saves changes to disk..."""
    lines = self.pendingfile.tolines()
    open(self.pendingfilename, "w").writelines(lines)
    self.pendingmtime = getmodtime(self.pendingfilename)

  def getstats(self):
    """reads the stats if neccessary or returns them from the cache"""
    if os.path.exists(self.statsfilename):
      self.readstats()
    pomtime = getmodtime(self.filename)
    pendingmtime = getmodtime(self.pendingfilename, None)
    if hasattr(self, "pendingmtime"):
      self.readpendingfile()
    if pomtime != getattr(self, "statspomtime", None) or pendingmtime != getattr(self, "statspendingmtime", None):
      self.calcstats()
      self.savestats()
    return self.stats

  def readstats(self):
    """reads the stats from the associated stats file, setting the required variables"""
    statsmtime = getmodtime(self.statsfilename)
    if statsmtime == getattr(self, "statsmtime", None):
      return
    stats = open(self.statsfilename, "r").read()
    mtimes, postatsstring = stats.split("\n", 1)
    mtimes = mtimes.strip().split()
    if len(mtimes) == 1:
      frompomtime = int(mtimes[0])
      frompendingmtime = None
    elif len(mtimes) == 2:
      frompomtime = int(mtimes[0])
      frompendingmtime = int(mtimes[1])
    postats = {}
    for line in postatsstring.split("\n"):
      if not line.strip():
        continue
      if not ":" in line:
        print "invalid stats line in", self.statsfilename,line
        continue
      name, count = line.split(":", 1)
      count = int(count.strip())
      postats[name.strip()] = count
    # save all the read times, data simultaneously
    self.statspomtime, self.statspendingmtime, self.statsmtime, self.stats = frompomtime, frompendingmtime, statsmtime, postats

  def savestats(self):
    """saves the current statistics to file"""
    # assumes self.stats is up to date
    try:
      postatsstring = "\n".join(["%s:%d" % (name, count) for name, count in self.stats.iteritems()])
      statsfile = open(self.statsfilename, "w")
      if os.path.exists(self.pendingfilename):
        statsfile.write("%d %d\n" % (getmodtime(self.filename), getmodtime(self.pendingfilename)))
      else:
        statsfile.write("%d\n" % getmodtime(self.filename))
      statsfile.write(postatsstring)
      statsfile.close()
    except IOError:
      # TODO: log a warning somewhere. we don't want an error as this is an optimization
      pass

  def calcstats(self):
    """calculates translation statistics for the given po file"""
    self.pofreshen()
    postats = dict([(name, len(items)) for name, items in self.classify.iteritems()])
    self.stats = postats

  def getassigns(self):
    """reads the assigns if neccessary or returns them from the cache"""
    if os.path.exists(self.assignsfilename):
      self.assigns = self.readassigns()
    else:
      self.assigns = {}
    return self.assigns

  def readassigns(self):
    """reads the assigns from the associated assigns file, returning the assigns
    the format is a number of lines consisting of
    username: action: itemranges
    where itemranges is a comma-separated list of item numbers or itemranges like 3-5
    e.g.  pootlewizz: review: 2-99,101"""
    assignsmtime = getmodtime(self.assignsfilename)
    if assignsmtime == getattr(self, "assignsmtime", None):
      return
    assignsstring = open(self.assignsfilename, "r").read()
    poassigns = {}
    for line in assignsstring.split("\n"):
      if not line.strip():
        continue
      if not line.count(":") == 2:
        print "invalid assigns line in", self.assignsfilename, line
        continue
      username, action, itemranges = line.split(":", 2)
      username, action = username.strip(), action.strip()
      if not username in poassigns:
        poassigns[username] = {}
      userassigns = poassigns[username]
      if not action in userassigns:
        userassigns[action] = []
      items = userassigns[action]
      for itemrange in itemranges.split(","):
        if "-" in itemrange:
          if not line.count("-") == 1:
            print "invalid assigns range in", self.assignsfilename, line, itemrange
            continue
          itemstart, itemstop = [int(item.strip()) for item in itemrange.split("-", 1)]
          items.extend(range(itemstart, itemstop+1))
        else:
          item = int(itemrange.strip())
          items.append(item)
      userassigns[action] = items
    return poassigns

  def assignto(self, item, username, action):
    """assigns the item to the given username for the given action"""
    userassigns = self.assigns.setdefault(username, {})
    items = userassigns.setdefault(action, [])
    if item not in items:
      items.append(item)
    self.saveassigns()

  def unassign(self, item, username, action=None):
    """removes assignments of the item to the given username for the given action (or all actions)"""
    userassigns = self.assigns.setdefault(username, {})
    if action is None:
      itemlist = [userassigns.get(action, []) for action in userassigns]
    else:
      itemlist = [userassigns.get(action, [])]
    for items in itemlist:
      if item in items:
        items.remove(item)
    self.saveassigns()

  def saveassigns(self):
    """saves the current assigns to file"""
    # assumes self.assigns is up to date
    assignstrings = []
    usernames = self.assigns.keys()
    usernames.sort()
    for username in usernames:
      actions = self.assigns[username].keys()
      actions.sort()
      for action in actions:
        items = self.assigns[username][action]
        items.sort()
        if items:
          lastitem = None
          rangestart = None
          assignstring = "%s: %s: " % (username, action)
          for item in items:
            if item - 1 == lastitem:
              if rangestart is None:
                rangestart = lastitem
            else:
              if rangestart is not None:
                assignstring += "-%d" % lastitem
                rangestart = None
              if lastitem is None:
                assignstring += "%d" % item
              else:
                assignstring += ",%d" % item
            lastitem = item
          if rangestart is not None:
            assignstring += "-%d" % lastitem
          assignstrings.append(assignstring + "\n")
    assignsfile = open(self.assignsfilename, "w")
    assignsfile.writelines(assignstrings)
    assignsfile.close()

  def setmsgstr(self, item, newmsgstr):
    """updates a translation with a new msgstr value"""
    self.pofreshen()
    thepo = self.transelements[item]
    thepo.msgstr = newmsgstr
    thepo.markfuzzy(False)
    self.savepofile()
    self.reclassifyelement(item)

  def classifyelements(self):
    """makes a dictionary of which elements fall into which classifications"""
    self.classify = {}
    self.classify["fuzzy"] = []
    self.classify["blank"] = []
    self.classify["translated"] = []
    self.classify["has-suggestion"] = []
    self.classify["total"] = []
    for checkname in self.checker.getfilters().keys():
      self.classify["check-" + checkname] = []
    for item, poel in enumerate(self.transelements):
      classes = self.classifyelement(poel)
      if self.getsuggestions(item):
        classes.append("has-suggestion")
      for classname in classes:
        if classname in self.classify:
          self.classify[classname].append(item)
        else:
          self.classify[classname] = item

  def classifyelement(self, poel):
    """returns all classify keys that this element should match"""
    classes = ["total"]
    if poel.isfuzzy():
      classes.append("fuzzy")
    if poel.isblankmsgstr():
      classes.append("blank")
    if not ("fuzzy" in classes or "blank" in classes):
      classes.append("translated")
    unquotedid = po.getunquotedstr(poel.msgid, joinwithlinebreak=False)
    unquotedstr = po.getunquotedstr(poel.msgstr, joinwithlinebreak=False)
    if isinstance(unquotedid, str) and isinstance(unquotedstr, unicode):
      unquotedid = unquotedid.decode("utf-8")
    failures = self.checker.run_filters(poel, unquotedid, unquotedstr)
    for failure in failures:
      functionname = failure.split(":",2)[0]
      classes.append("check-" + functionname)
    return classes

  def reclassifyelement(self, item):
    """updates the classification of poel in self.classify"""
    poel = self.transelements[item]
    classes = self.classifyelement(poel)
    if self.getsuggestions(item):
      classes.append("has-suggestion")
    for classname, matchingitems in self.classify.items():
      if (classname in classes) != (item in matchingitems):
        if classname in classes:
          self.classify[classname].append(item)
        else:
          self.classify[classname].remove(item)
        self.classify[classname].sort()
    self.calcstats()
    self.savestats()

  def reclassifysuggestions(self):
    """shortcut to only update classification of has-suggestion for all items"""
    suggitems = []
    suggsources = {}
    for thesugg in self.pendingfile.poelements:
      sources = tuple(thesugg.getsources())
      suggsources[sources] = thesugg
    suggitems = [item for item in self.transelements if tuple(item.getsources()) in suggsources]
    havesuggestions = self.classify["has-suggestion"]
    for item, poel in enumerate(self.transelements):
      if (poel in suggitems) != (item in havesuggestions):
        if poel in suggitems:
          havesuggestions.append(item)
        else:
          havesuggestions.remove(item)
        havesuggestions.sort()
    self.calcstats()
    self.savestats()

  def getsuggestions(self, item):
    """find all the suggestion items submitted for the given (pofile or pofilename) and item"""
    self.readpendingfile()
    thepo = self.transelements[item]
    sources = thepo.getsources()
    # TODO: review the matching method
    suggestpos = [suggestpo for suggestpo in self.pendingfile.poelements if suggestpo.getsources() == sources]
    return suggestpos

  def addsuggestion(self, item, suggmsgstr, username):
    """adds a new suggestion for the given item to the pendingfile"""
    self.readpendingfile()
    thepo = self.transelements[item]
    newpo = thepo.copy()
    if username is not None:
      newpo.msgidcomments.append('"_: suggested by %s"' % username)
    newpo.msgstr = suggmsgstr
    newpo.markfuzzy(False)
    self.pendingfile.poelements.append(newpo)
    self.savependingfile()
    self.reclassifyelement(item)

  def deletesuggestion(self, item, suggitem):
    """removes the suggestion from the pending file"""
    self.readpendingfile()
    # TODO: remove the suggestion in a less brutal manner
    del self.pendingfile.poelements[suggitem]
    self.savependingfile()
    self.reclassifyelement(item)

  def iteritems(self, search, lastitem=None):
    """iterates through the items in this pofile starting after the given lastitem, using the given search"""
    # update stats if required
    self.getstats()
    if lastitem is None:
      minitem = 0
    else:
      minitem = lastitem + 1
    maxitem = len(self.transelements)
    validitems = range(minitem, maxitem)
    if search.assignedto or search.assignedaction: 
      # filter based on assign criteria
      self.getassigns()
      if search.assignedto:
        usernames = [search.assignedto]
      else:
        usernames = self.assigns.iterkeys()
      assignitems = []
      for username in usernames:
        if search.assignedaction:
          actionitems = self.assigns[username].get(search.assignedaction, [])
          assignitems.extend(actionitems)
        else:
          for actionitems in self.assigns[username].itervalues():
            assignitems.extend(actionitems)
      validitems = [item for item in validitems if item in assignitems]
    # loop through, filtering on matchnames if required
    for item in validitems:
      if not search.matchnames:
        yield item
      for name in search.matchnames:
        if item in self.classify[name]:
          yield item

class Search:
  """an object containint all the searching information"""
  def __init__(self, dirfilter=None, matchnames=[], assignedto=None, assignedaction=None, searchtext=None):
    self.dirfilter = dirfilter
    self.matchnames = matchnames
    self.assignedto = assignedto
    self.assignedaction = assignedaction
    self.searchtext = searchtext

class potimecache(timecache.timecache):
  """caches pootlefile objects, remembers time, and reverts back to statistics when neccessary..."""
  def __init__(self, expiryperiod, project):
    """initialises the cache to keep objects for the given expiryperiod, and point back to the project"""
    timecache.timecache.__init__(self, expiryperiod)
    self.project = project

  def expire(self, pofilename):
    """expires the given pofilename by recreating it (holding only stats)"""
    timestamp, currentfile = dict.__getitem__(self, pofilename)
    if currentfile.pomtime is not None:
      # use the currentfile.pomtime as a timestamp as well, so any modifications will extend its life
      if time.time() - currentfile.pomtime > self.expiryperiod.seconds:
        self.__setitem__(pofilename, pootlefile(self.project, pofilename))
 
class TranslationProject:
  """Manages iterating through the translations in a particular project"""
  def __init__(self, languagecode, projectcode, potree, create=False):
    self.languagecode = languagecode
    self.projectcode = projectcode
    self.potree = potree
    self.languagename = self.potree.getlanguagename(self.languagecode)
    self.projectname = self.potree.getprojectname(self.projectcode)
    self.projectdescription = self.potree.getprojectdescription(self.projectcode)
    self.pofiles = potimecache(15*60, self)
    self.projectcheckerstyle = self.potree.getprojectcheckerstyle(self.projectcode)
    checkerclasses = [checks.projectcheckers.get(self.projectcheckerstyle, checks.StandardChecker), pofilter.StandardPOChecker]
    self.checker = pofilter.POTeeChecker(checkerclasses=checkerclasses, errorhandler=self.filtererrorhandler)
    if create:
      self.create()
    self.podir = potree.getpodir(languagecode, projectcode)
    if self.potree.hasgnufiles(self.podir, self.languagecode):
      self.filestyle = "gnu"
    else:
      self.filestyle = "std"
    self.scanpofiles()
    self.initindex()

  def scanpofiles(self):
    """sets the list of pofilenames by scanning the project directory"""
    self.pofilenames = self.potree.getpofiles(self.languagecode, self.projectcode)
    for pofilename in self.pofilenames:
      if not pofilename in self.pofiles:
        self.pofiles[pofilename] = pootlefile(self, pofilename)
    # remove any files that have been deleted since initialization
    for pofilename in self.pofiles.keys():
      if not pofilename in self.pofilenames:
        del self.pofiles[pofilename]

  def addnewpofile(self, dirname, pofilename, contents):
    """creates a new po file with the given contents"""
    if os.path.isabs(dirname) or dirname.startswith("."):
      raise ValueError("invalid/insecure file path: %s" % dirname)
    if os.path.basename(pofilename) != pofilename or pofilename.startswith("."):
      raise ValueError("invalid/insecure file name: %s" % pofilename)
    if self.filestyle == "gnu":
      if not self.potree.languagematch(self.languagecode, pofilename[:-len(".po")]):
        raise ValueError("invalid GNU-style file name %s: must match '%s.po' or '%s[_-][A-Z]{2,3}.po'" % (pofilename, self.languagecode, self.languagecode))
    dircheck = self.podir
    for part in dirname.split(os.sep):
      dircheck = os.path.join(dircheck, part)
      if dircheck and not os.path.isdir(dircheck):
        os.mkdir(dircheck)
    pathname = os.path.join(self.podir, dirname, pofilename)
    if os.path.exists(pathname):
      raise ValueError("that file already exists")
    pofile = open(pathname, "wb")
    pofile.write(contents)
    pofile.close()
    self.scanpofiles()

  def create(self):
    projectdir = os.path.join(self.potree.podirectory, self.projectcode)
    templatesdir = os.path.join(projectdir, "templates")
    if self.potree.isgnustyle(self.projectcode):
      self.filestyle = "gnu"
    else:
      self.filestyle = "std"
    if not os.path.exists(templatesdir):
      templatesdir = projectdir
    templates = self.potree.gettemplates(self.projectcode)
    if self.filestyle == "gnu":
      self.podir = projectdir
      if not templates:
        raise NotImplementedError("Cannot create GNU-style translation project without templates")
    else:
      self.podir = os.path.join(projectdir, self.languagecode)
      if not os.path.exists(self.podir):
        os.mkdir(self.podir)
    for potfilename in templates:
      inputfile = open(os.path.join(templatesdir, potfilename), "rb")
      outputfile = cStringIO.StringIO()
      pot2po.convertpot(inputfile, outputfile, None)
      dirname, potfilename = os.path.dirname(potfilename), os.path.basename(potfilename)
      if self.filestyle == "gnu":
        pofilename = self.languagecode + os.extsep + "po"
      else:
        pofilename = potfilename[:-len(os.extsep+"pot")] + os.extsep + "po"
      self.addnewpofile(dirname, pofilename, outputfile.getvalue())

  def filtererrorhandler(self, functionname, str1, str2, e):
    print "error in filter %s: %r, %r, %s" % (functionname, str1, str2, e)
    return False

  def getarchive(self, pofilenames):
    """returns an archive of the given filenames"""
    tempzipfile = os.tmpnam()
    try:
      # using zip command line is fast
      os.system("cd %s ; zip -r - %s > %s" % (self.podir, " ".join(pofilenames), tempzipfile))
      return open(tempzipfile, "r").read()
    finally:
      if os.path.exists(tempzipfile):
        os.remove(tempzipfile)
    # but if it doesn't work, we can do it from python
    import cStringIO, zipfile
    archivecontents = cStringIO.StringIO()
    archive = zipfile.ZipFile(archivecontents, 'w', zipfile.ZIP_DEFLATED)
    for pofilename in pofilenames:
      pofile = self.getpofile(pofilename)
      archive.write(pofile.filename, pofilename)
    archive.close()
    return archivecontents.getvalue()

  def uploadarchive(self, dirname, archivecontents):
    """uploads the files inside the archive"""
    try:
      tempzipfile = os.tmpnam()
      # using zip command line is fast
      # os.system("cd %s ; zip -r - %s > %s" % (self.podir, " ".join(pofilenames), tempzipfile))
      # return open(tempzipfile, "r").read()
      pass
    finally:
      if os.path.exists(tempzipfile):
        os.remove(tempzipfile)
    # but if it doesn't work, we can do it from python
    import cStringIO, zipfile
    archivefile = cStringIO.StringIO(archivecontents)
    archive = zipfile.ZipFile(archivefile, 'r')
    # TODO: find a better way to return errors...
    for filename in archive.namelist():
      if not filename.endswith(os.extsep + "po"):
        print "error adding %s: not a .po file" % filename
        continue
      pathname = os.path.join(self.podir, dirname, filename)
      contents = archive.read(filename)
      subdirname, pofilename = os.path.dirname(filename), os.path.basename(filename)
      try:
        # TODO: use zipfile info to set the time and date of the file
        self.addnewpofile(os.path.join(dirname, subdirname), pofilename, contents)
      except ValueError, e:
        print "error adding %s" % filename, e
        continue
    archive.close()

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

  def initindex(self):
    """initializes the search index"""
    if PyLucene is None:
      return
    self.indexdir = os.path.join(self.podir, ".poindex-%s-%s" % (self.projectcode, self.languagecode))
    self.analyzer = PyLucene.StandardAnalyzer()
    if not os.path.exists(self.indexdir):
      os.mkdir(self.indexdir)
      self.indexstore = PyLucene.FSDirectory.getDirectory(self.indexdir, True)
      writer = PyLucene.IndexWriter(self.indexstore, self.analyzer, True)
      writer.close()
    else:
      self.indexstore = PyLucene.FSDirectory.getDirectory(self.indexdir, False)
    self.indexreader = PyLucene.IndexReader.open(self.indexstore)
    self.searcher = PyLucene.IndexSearcher(self.indexreader)
    addlist, deletelist = [], []
    for pofilename in self.pofiles:
      self.updateindex(pofilename, addlist, deletelist)
    # TODO: this is all unneccessarily complicated, there must be a simpler way.
    if deletelist:
      for docid in deletelist:
        self.indexreader.deleteDocument(docid)
      self.searcher.close()
      self.indexreader.close()
    if addlist:
      self.indexwriter = PyLucene.IndexWriter(self.indexstore, self.analyzer, False)
      for doc in addlist:
        self.indexwriter.addDocument(doc)
      self.indexwriter.optimize(True)
      self.indexwriter.close()
    if deletelist:
      self.indexreader = PyLucene.IndexReader.open(self.indexstore)
      self.searcher = PyLucene.IndexSearcher(self.indexreader)

  def updateindex(self, pofilename, addlist, deletelist):
    """updates the index with the contents of pofilename"""
    if PyLucene is None:
      return
    needsupdate = True
    pofile = self.pofiles[pofilename]
    presencecheck = PyLucene.QueryParser.parse(pofilename, "filename", self.analyzer)
    hits = self.searcher.search(presencecheck)
    pomtime = getmodtime(pofile.filename)
    for hit in xrange(hits.length()):
      doc = hits.doc(hit)
      if doc.get("pomtime") == str(pomtime):
        needsupdate = False
    if needsupdate:
      # TODO: update this to index items individually rather than the whole file
      for hit in xrange(hits.length()):
        docid = hits.id(hit)
        deletelist.append(docid)
      pofile.pofreshen()
      doc = PyLucene.Document()
      doc.add(PyLucene.Field("filename", pofilename, True, True, True))
      doc.add(PyLucene.Field("pomtime", str(pomtime), True, True, True))
      allorig, alltrans = [], []
      for thepo in pofile.transelements:
        orig, trans = self.unquotefrompo(thepo.msgid), self.unquotefrompo(thepo.msgstr)
        allorig.append(orig)
        alltrans.append(trans)
      allorig = "\n".join(allorig)
      alltrans = "\n".join(alltrans)
      doc.add(PyLucene.Field("orig", allorig, False, True, True))
      doc.add(PyLucene.Field("trans", alltrans, False, True, True))
      addlist.append(doc)

  def matchessearch(self, pofilename, search):
    """returns whether any items in the pofilename match the search (based on collected stats etc)"""
    if search.dirfilter is not None and not pofilename.startswith(search.dirfilter):
      return False
    if search.assignedto or search.assignedaction:
      assigns = self.pofiles[pofilename].getassigns()
      if search.assignedto is not None:
        if search.assignedto not in assigns:
          return False
        assigns = assigns[search.assignedto]
      else:
        assigns = reduce(lambda x, y: x+y, [userassigns.keys() for userassigns in assigns.values()], [])
      if search.assignedaction is not None:
        if search.assignedaction not in assigns:
          return False
    if search.matchnames:
      postats = self.getpostats(pofilename)
      matches = False
      for name in search.matchnames:
        if postats[name]:
          matches = True
      if not matches:
        return False
    if PyLucene and search.searchtext:
      # TODO: move this up a level, use index to manage whole search
      origquery = PyLucene.QueryParser.parse(search.searchtext, "orig", self.analyzer)
      transquery = PyLucene.QueryParser.parse(search.searchtext, "trans", self.analyzer)
      textquery = PyLucene.BooleanQuery()
      textquery.add(origquery, False, False)
      textquery.add(transquery, False, False)
      hits = self.searcher.search(textquery)
      for hit in xrange(hits.length()):
        if hits.doc(hit).get("filename") == pofilename:
          return True
      return False
    return True

  def searchpofilenames(self, lastpofilename, search, includelast=False):
    """find the next pofilename that has items matching the given search"""
    for pofilename in self.iterpofilenames(lastpofilename, includelast):
      if self.matchessearch(pofilename, search):
        yield pofilename

  def searchpoitems(self, pofilename, item, search):
    """finds the next item matching the given search"""
    if search.searchtext:
      pogrepfilter = pogrep.pogrepfilter(search.searchtext, None, ignorecase=True)
    for pofilename in self.searchpofilenames(pofilename, search, includelast=True):
      pofile = self.getpofile(pofilename)
      for item in pofile.iteritems(search, item):
        # TODO: move this to iteritems
        if search.searchtext:
          thepo = pofile.transelements[item]
          if pogrepfilter.filterelement(thepo):
            yield pofilename, item
        else:
          yield pofilename, item

  def assignpoitems(self, search, assignto, action):
    """assign all the items matching the search to the assignto user with the given action"""
    if search.searchtext:
      pogrepfilter = pogrep.pogrepfilter(search.searchtext, None, ignorecase=True)
    assigncount = 0
    for pofilename in self.searchpofilenames(None, search, includelast=True):
      pofile = self.getpofile(pofilename)
      for item in pofile.iteritems(search, None):
        # TODO: move this to iteritems
        if search.searchtext:
          thepo = pofile.transelements[item]
          if pogrepfilter.filterelement(thepo):
            pofile.assignto(item, assignto, action)
            assigncount += 1
        else:
          pofile.assignto(item, assignto, action)
          assigncount += 1
    return assigncount

  def unassignpoitems(self, search, assignedto, action=None):
    """unassigns all the items matching the search to the assignedto user"""
    if search.searchtext:
      pogrepfilter = pogrep.pogrepfilter(search.searchtext, None, ignorecase=True)
    assigncount = 0
    for pofilename in self.searchpofilenames(None, search, includelast=True):
      pofile = self.getpofile(pofilename)
      for item in pofile.iteritems(search, None):
        # TODO: move this to iteritems
        if search.searchtext:
          thepo = pofile.transelements[item]
          if pogrepfilter.filterelement(thepo):
            pofile.unassign(item, assignedto, action)
            assigncount += 1
        else:
          pofile.unassign(item, assignedto, action)
          assigncount += 1
    return assigncount

  def gettranslationsession(self, session):
    """gets the user's translationsession"""
    if not hasattr(session, "translationsessions"):
      session.translationsessions = {}
    if not (self.languagecode, self.projectcode) in session.translationsessions:
      session.translationsessions[self.languagecode, self.projectcode] = TranslationSession(self, session)
    return session.translationsessions[self.languagecode, self.projectcode]

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
      assignstats = self.getassignstats(pofilename)
      for name, count in assignstats.iteritems():
        totalstats["assign-"+name] = totalstats.get("assign-"+name, 0) + count
    return totalstats

  def track(self, pofilename, item, message):
    """sends a track message to the pofile"""
    self.pofiles[pofilename].track(item, message)

  def gettracks(self, pofilenames=None):
    """calculates translation statistics for the given po files (or all if None given)"""
    alltracks = []
    if pofilenames is None:
      pofilenames = self.pofilenames
    for pofilename in pofilenames:
      if not pofilename or os.path.isdir(pofilename):
        continue
      tracker = self.pofiles[pofilename].tracker
      items = tracker.keys()
      items.sort()
      for item in items:
        alltracks.append("%s item %d: %s" % (pofilename, item, tracker[item]))
    return alltracks

  def getpostats(self, pofilename):
    """calculates translation statistics for the given po file"""
    return self.pofiles[pofilename].getstats()

  def getassignstats(self, pofilename):
    """calculates translation statistics for the given po file"""
    assigns = self.pofiles[pofilename].getassigns()
    assignstats = {}
    for username, userassigns in assigns.iteritems():
      count = 0
      for action, items in userassigns.iteritems():
        count += len(items)
      assignstats[username] = count
    return assignstats
 
  def getpofile(self, pofilename):
    """parses the file into a pofile object and stores in self.pofiles"""
    pofile = self.pofiles[pofilename]
    pofile.pofreshen()
    return pofile

  def getpofilelen(self, pofilename):
    """returns number of items in the given pofilename"""
    # TODO: needn't parse the file for this ...
    pofile = self.getpofile(pofilename)
    return len(pofile.transelements)

  def getitem(self, pofilename, item):
    """returns a particular item from a particular po file's orig, trans strings as a tuple"""
    pofile = self.getpofile(pofilename)
    thepo = pofile.transelements[item]
    orig, trans = self.unquotefrompo(thepo.msgid), self.unquotefrompo(thepo.msgstr)
    return orig, trans

  def getitemclasses(self, pofilename, item):
    """returns which classes this item belongs to"""
    # TODO: needn't parse the file for this ...
    pofile = self.getpofile(pofilename)
    return [classname for (classname, classitems) in pofile.classify.iteritems() if item in classitems]

  def unquotefrompo(self, postr):
    """extracts a po-quoted string to normal text"""
    # TODO: handle plurals properly
    if isinstance(postr, dict):
      pokeys = postr.keys()
      pokeys.sort()
      return self.unquotefrompo(postr[pokeys[0]])
    return po.unquotefrompo(postr)

  def quoteforpo(self, text):
    """quotes text in po-style"""
    text = text.replace("\r\n", "\n")
    return po.quoteforpo(text)

  def getitems(self, pofilename, itemstart, itemstop):
    """returns a set of items from the pofile, converted to original and translation strings"""
    pofile = self.getpofile(pofilename)
    elements = pofile.transelements[max(itemstart,0):itemstop]
    return [(self.unquotefrompo(poel.msgid), self.unquotefrompo(poel.msgstr)) for poel in elements]

  def updatetranslation(self, pofilename, item, trans, username):
    """updates a translation with a new value..."""
    newmsgstr = self.quoteforpo(trans)
    pofile = self.pofiles[pofilename]
    pofile.track(item, "edited by %s" % username)
    pofile.setmsgstr(item, newmsgstr)

  def suggesttranslation(self, pofilename, item, trans, username):
    """stores a new suggestion for a translation..."""
    suggmsgstr = self.quoteforpo(trans)
    pofile = self.getpofile(pofilename)
    pofile.track(item, "suggestion made by %s" % username)
    pofile.addsuggestion(item, suggmsgstr, username)

  def getsuggestions(self, pofile, item):
    """find all the suggestions submitted for the given (pofile or pofilename) and item"""
    if isinstance(pofile, (str, unicode)):
      pofilename = pofile
      pofile = self.getpofile(pofilename)
    suggestpos = pofile.getsuggestions(item)
    suggestions = [self.unquotefrompo(suggestpo.msgstr) for suggestpo in suggestpos]
    return suggestions

  def acceptsuggestion(self, pofile, item, suggitem, newtrans, username):
    """accepts the suggestion into the main pofile"""
    if isinstance(pofile, (str, unicode)):
      pofilename = pofile
      pofile = self.getpofile(pofilename)
    pofile.track(item, "suggestion by %s accepted by %s" % (self.getsuggester(pofile, item, suggitem), username))
    pofile.deletesuggestion(item, suggitem)
    self.updatetranslation(pofilename, item, newtrans, username)

  def getsuggester(self, pofile, item, suggitem):
    """returns who suggested the given item's suggitem if recorded, else None"""
    if isinstance(pofile, (str, unicode)):
      pofilename = pofile
      pofile = self.getpofile(pofilename)
    suggestionpo = pofile.getsuggestions(item)[suggitem]
    for msgidcomment in suggestionpo.msgidcomments:
      if msgidcomment.find("suggested by ") != -1:
        suggestedby = po.getunquotedstr([msgidcomment]).replace("_:", "", 1).replace("suggested by ", "", 1).strip()
        return suggestedby
    return None

  def rejectsuggestion(self, pofile, item, suggitem, newtrans, username):
    """rejects the suggestion and removes it from the pending file"""
    if isinstance(pofile, (str, unicode)):
      pofilename = pofile
      pofile = self.getpofile(pofilename)
    pofile.track(item, "suggestion by %s rejected by %s" % (self.getsuggester(pofile, item, suggitem), username))
    pofile.deletesuggestion(item, suggitem)

  def savepofile(self, pofilename):
    """saves changes to disk..."""
    pofile = self.getpofile(pofilename)
    pofile.savepofile()

  def getsource(self, pofilename):
    """returns pofile source"""
    pofile = self.getpofile(pofilename)
    return pofile.getsource()

  def getcsv(self, csvfilename):
    """returns pofile as csv"""
    pofilename = csvfilename.replace(".csv", ".po")
    pofile = self.getpofile(pofilename)
    return pofile.getcsv()

  def getmo(self, mofilename):
    """return pofile as compiled mo"""
    pofilename = mofilename.replace(".mo", ".po")
    pofile = self.getpofile(pofilename)
    return pofile.getmo()

  def gettext(self, message):
    """uses the project as a live translator for the given message"""
    for pofilename, pofile in self.pofiles.iteritems():
      if pofile.pomtime != getmodtime(pofile.filename):
        pofile.readpofile()
        pofile.makeindex()
      elif not hasattr(pofile, "msgidindex"):
        pofile.makeindex()
      thepo = pofile.msgidindex.get(message, None)
      if not thepo or thepo.isblankmsgstr():
        continue
      tmsg = po.unquotefrompo(thepo.msgstr)
      if tmsg is not None:
        return tmsg
    return message

  def ugettext(self, message):
    """gets the translation of the message by searching through all the pofiles (unicode version)"""
    for pofilename, pofile in self.pofiles.iteritems():
      try:
        if pofile.pomtime != getmodtime(pofile.filename):
          pofile.readpofile()
          pofile.makeindex()
        elif not hasattr(pofile, "msgidindex"):
          pofile.makeindex()
        thepo = pofile.msgidindex.get(message, None)
        if not thepo or thepo.isblankmsgstr():
          continue
        tmsg = po.unquotefrompo(thepo.msgstr)
        if tmsg is not None:
          if isinstance(tmsg, unicode):
            return tmsg
          else:
            return unicode(tmsg, pofile.encoding)
      except Exception, e:
        print "error reading translation from pofile %s: %s" % (pofilename, e)
    return unicode(message)

  def hascreatemofiles(self, projectcode):
    """returns whether the project has createmofile set"""
    return self.potree.getprojectcreatemofiles(projectcode) == 1

class POTree:
  """Manages the tree of projects and languages"""
  def __init__(self, instance):
    self.languages = instance.languages
    self.projects = instance.projects
    self.podirectory = instance.podirectory
    self.projectcache = {}

  def saveprefs(self):
    """saves any changes made to the preferences"""
    # TODO: this is a hack, fix it up nicely :-)
    prefsfile = self.languages.__root__.__dict__["_setvalue"].im_self
    prefsfile.savefile()

  def changelanguages(self, argdict):
    """changes language entries"""
    for key, value in argdict.iteritems():
      if key.startswith("languageremove-"):
        languagecode = key.replace("languageremove-", "", 1)
        if self.haslanguage(languagecode):
          delattr(self.languages, languagecode)
      elif key.startswith("languagename-"):
        languagecode = key.replace("languagename-", "", 1)
        if self.haslanguage(languagecode):
          languagename = self.getlanguagename(languagecode)
          if languagename != value:
            self.setlanguagename(languagecode, value)
      elif key == "newlanguagecode":
        languagecode = value.lower()
        if not languagecode.strip():
          continue
        if not languagecode.isalpha():
          raise ValueError("Language code must be alphabetic")
        if self.haslanguage(languagecode):
          raise ValueError("Already have language with the code %s" % languagecode)
        languagename = argdict.get("newlanguagename", languagecode)
        setattr(self.languages, languagecode + ".fullname", languagename)
    self.saveprefs()

  def changeprojects(self, argdict):
    """changes project entries"""
    for key, value in argdict.iteritems():
      if key.startswith("projectremove-"):
        projectcode = key.replace("projectremove-", "", 1)
        if hasattr(self.projects, projectcode):
          delattr(self.projects, projectcode)
      elif key.startswith("projectname-"):
        projectcode = key.replace("projectname-", "", 1)
        if hasattr(self.projects, projectcode):
          projectname = self.getprojectname(projectcode)
          if projectname != value:
            self.setprojectname(projectcode, value)
      elif key.startswith("projectdescription-"):
        projectcode = key.replace("projectdescription-", "", 1)
        if hasattr(self.projects, projectcode):
          projectdescription = self.getprojectdescription(projectcode)
          if projectdescription != value:
            self.setprojectdescription(projectcode, value)
      elif key.startswith("projectcheckerstyle-"):
        projectcode = key.replace("projectcheckerstyle-", "", 1)
        if hasattr(self.projects, projectcode):
          projectcheckerstyle = self.getprojectcheckerstyle(projectcode)
          if projectcheckerstyle != value:
            self.setprojectcheckerstyle(projectcode, value)
      elif key.startswith("projectcreatemofiles-"):
        projectcode = key.replace("projectcreatemofiles-", "", 1)
        if hasattr(self.projects, projectcode):
          self.setprojectcreatemofiles(projectcode, 1)
      elif key == "newprojectcode":
        projectcode = value.lower()
        if not projectcode:
          continue
        if not (projectcode[:1].isalpha() and projectcode.replace("_","").isalnum()):
          raise ValueError("Project code must be alphanumeric and start with an alphabetic character (got %r)" % projectcode)
        if hasattr(self.projects, projectcode):
          raise ValueError("Already have project with the code %s" % projectcode)
        projectname = argdict.get("newprojectname", projectcode)
        projectdescription = argdict.get("newprojectdescription", "")
        projectcheckerstyle = argdict.get("newprojectcheckerstyle", "")
        projectcreatemofiles = argdict.get("newprojectcreatemofiles", "")
        setattr(self.projects, projectcode + ".fullname", projectname)
        setattr(self.projects, projectcode + ".description", projectdescription)
        setattr(self.projects, projectcode + ".checkerstyle", projectcheckerstyle)
        setattr(self.projects, projectcode + ".createmofiles", projectcreatemofiles)
        projectdir = os.path.join(self.podirectory, projectcode)
        if not os.path.isdir(projectdir):
          os.mkdir(projectdir)
    self.saveprefs()

  def haslanguage(self, languagecode):
    """checks if this language exists"""
    return hasattr(self.languages, languagecode)

  def getlanguageprefs(self, languagecode):
    """returns the language object"""
    return getattr(self.languages, languagecode)

  def getlanguagename(self, languagecode):
    """returns the language's full name"""
    return getattr(self.getlanguageprefs(languagecode), "fullname", languagecode)

  def setlanguagename(self, languagecode, languagename):
    """returns the language's full name"""
    setattr(self.getlanguageprefs(languagecode), "fullname", languagename)

  def getlanguagecodes(self, projectcode=None):
    """returns a list of valid languagecodes for a given project or all projects"""
    alllanguagecodes = [languagecode for languagecode, language in self.languages.iteritems()]
    if projectcode is None:
      alllanguagecodes.sort()
      return alllanguagecodes
    else:
      projectdir = os.path.join(self.podirectory, projectcode)
      if not os.path.exists(projectdir):
        return []
      if self.isgnustyle(projectcode):
        return [languagecode for languagecode in alllanguagecodes if self.hasproject(languagecode, projectcode)]
      else:
        subdirs = [fn for fn in os.listdir(projectdir) if os.path.isdir(os.path.join(projectdir, fn))]
        languagecodes = []
        for potentialcode in subdirs:
          if not self.languagematch(None, potentialcode):
            continue
          if "-" in potentialcode:
            potentialcode = potentialcode[:potentialcode.find("-")]
          elif "_" in potentialcode:
            potentialcode = potentialcode[:potentialcode.find("_")]
          if potentialcode in alllanguagecodes:
            languagecodes.append(potentialcode)
        return languagecodes

  def getprojectcodes(self, languagecode=None):
    """returns a list of project codes that are valid for the given languagecode or all projects"""
    projectcodes = [projectcode for projectcode, projectprefs in self.projects.iteritems()]
    projectcodes.sort()
    if languagecode is None:
      return projectcodes
    else:
      return [projectcode for projectcode in projectcodes if self.hasproject(languagecode, projectcode)]

  def hasproject(self, languagecode, projectcode):
    """returns whether the project exists for the language"""
    if not hasattr(self.projects, projectcode):
      return False
    if languagecode is None:
      return True
    if not self.haslanguage(languagecode):
      return False
    try:
      podir = self.getpodir(languagecode, projectcode)
      return True
    except IndexError:
      return False

  def gettemplates(self, projectcode):
    """returns templates for the given project"""
    projectdir = os.path.join(self.podirectory, projectcode)
    templatesdir = os.path.join(projectdir, "templates")
    if not os.path.exists(templatesdir):
      templatesdir = projectdir
    potfilenames = []
    def addfiles(podir, dirname, fnames):
      """adds the files to the set of files for this project"""
      basedirname = dirname.replace(podir, "", 1)
      while basedirname.startswith(os.sep):
        basedirname = basedirname.replace(os.sep, "", 1)
      ponames = [fname for fname in fnames if fname.endswith(os.extsep+"pot")]
      potfilenames.extend([os.path.join(basedirname, poname) for poname in ponames])
    os.path.walk(templatesdir, addfiles, templatesdir)
    return potfilenames

  def getproject(self, languagecode, projectcode):
    """returns the project object for the languagecode and projectcode"""
    if (languagecode, projectcode) not in self.projectcache:
      self.projectcache[languagecode, projectcode] = TranslationProject(languagecode, projectcode, self)
    return self.projectcache[languagecode, projectcode]

  def isgnustyle(self, projectcode):
    """checks whether the whole project is a GNU-style project"""
    projectdir = os.path.join(self.podirectory, projectcode)
    return self.hasgnufiles(projectdir)

  def addtranslationproject(self, languagecode, projectcode):
    """creates a new TranslationProject"""
    if self.hasproject(languagecode, projectcode):
      raise ValueError("TranslationProject for project %s, language %s already exists" % (projectcode, languagecode))
    translationproject = TranslationProject(languagecode, projectcode, self, create=True)

  def getprojectname(self, projectcode):
    """returns the full name of the project"""
    projectprefs = getattr(self.projects, projectcode)
    return getattr(projectprefs, "fullname", projectcode)

  def setprojectname(self, projectcode, projectname):
    """returns the full name of the project"""
    projectprefs = getattr(self.projects, projectcode)
    setattr(projectprefs, "fullname", projectname)

  def getprojectdescription(self, projectcode):
    """returns the project description"""
    projectprefs = getattr(self.projects, projectcode)
    return getattr(projectprefs, "description", projectcode)

  def setprojectdescription(self, projectcode, projectdescription):
    """returns the project description"""
    projectprefs = getattr(self.projects, projectcode)
    setattr(projectprefs, "description", projectdescription)

  def getprojectcheckerstyle(self, projectcode):
    """returns the project checker style"""
    projectprefs = getattr(self.projects, projectcode)
    return getattr(projectprefs, "checkerstyle", projectcode)

  def setprojectcheckerstyle(self, projectcode, projectcheckerstyle):
    """sets the project checker style"""
    projectprefs = getattr(self.projects, projectcode)
    setattr(projectprefs, "checkerstyle", projectcheckerstyle)

  def getprojectcreatemofiles(self, projectcode):
    """returns whether the project builds MO files"""
    projectprefs = getattr(self.projects, projectcode)
    return getattr(projectprefs, "createmofiles", False)

  def setprojectcreatemofiles(self, projectcode, projectcreatemofiles):
    """sets whether the project builds MO files"""
    projectprefs = getattr(self.projects, projectcode)
    setattr(projectprefs, "createmofiles", projectcreatemofiles)

  def hasgnufiles(self, podir, languagecode=None):
    """returns whether this directory contains gnu-style PO filenames for the given language"""
    fnames = os.listdir(podir)
    poext = os.extsep + "po"
    subdirs = []
    for fn in fnames:
      if fn.endswith(poext):
        if self.languagematch(languagecode, fn[:-len(poext)]):
          return True
      elif os.path.isdir(os.path.join(podir, fn)):
        # if we have a language subdirectory, we're probably not GNU-style
        if self.languagematch(languagecode, fn):
          return False
        subdirs.append(os.path.join(podir, fn))
    for subdir in subdirs:
      if self.hasgnufiles(subdir, languagecode):
        return True
    return False

  def getpodir(self, languagecode, projectcode):
    """returns the base directory containing po files for the project"""
    projectdir = os.path.join(self.podirectory, projectcode)
    if not os.path.exists(projectdir):
      raise IndexError("directory not found for project %s" % (projectcode))
      return None
    languagedir = os.path.join(projectdir, languagecode)
    if not os.path.exists(languagedir):
      languagedirs = [languagedir for languagedir in os.listdir(projectdir) if self.languagematch(languagecode, languagedir)]
      if not languagedirs:
        # if no matching directories can be found, check if it is a GNU-style project
        if self.hasgnufiles(projectdir, languagecode):
          return projectdir
        raise IndexError("directory not found for language %s, project %s" % (languagecode, projectcode))
      # TODO: handle multiple regions
      if len(languagedirs) > 1:
        raise IndexError("multiple regions defined for language %s, project %s" % (languagecode, projectcode))
      languagedir = os.path.join(projectdir, languagedirs[0])
    return languagedir

  def languagematch(self, languagecode, otherlanguagecode):
    """matches a languagecode to another, ignoring regions in the second"""
    if languagecode is None:
      return languagere.match(otherlanguagecode)
    return languagecode == otherlanguagecode or \
      (otherlanguagecode.startswith(languagecode) and regionre.match(otherlanguagecode[len(languagecode):]))

  def getpofiles(self, languagecode, projectcode):
    """returns a list of po files for the project and language"""
    def addfiles(podir, dirname, fnames):
      """adds the files to the set of files for this project"""
      basedirname = dirname.replace(podir, "", 1)
      while basedirname.startswith(os.sep):
        basedirname = basedirname.replace(os.sep, "", 1)
      ponames = [fname for fname in fnames if fname.endswith(os.extsep+"po")]
      pofilenames.extend([os.path.join(basedirname, poname) for poname in ponames])
    def addgnufiles(podir, dirname, fnames):
      """adds the files to the set of files for this project"""
      basedirname = dirname.replace(podir, "", 1)
      while basedirname.startswith(os.sep):
        basedirname = basedirname.replace(os.sep, "", 1)
      poext = os.extsep + "po"
      ponames = [fn for fn in fnames if fn.endswith(poext) and self.languagematch(languagecode, fn[:-len(poext)])]
      pofilenames.extend([os.path.join(basedirname, poname) for poname in ponames])
    pofilenames = []
    podir = self.getpodir(languagecode, projectcode)
    if self.hasgnufiles(podir, languagecode):
      os.path.walk(podir, addgnufiles, podir)
    else:
      os.path.walk(podir, addfiles, podir)
    return pofilenames

  def refreshstats(self):
    """manually refreshes (all or missing) the stats files"""
    for projectcode in self.getprojectcodes():
      print "Project %s:" % (projectcode)
      for languagecode in self.getlanguagecodes(projectcode):
        print "Project %s, Language %s:" % (projectcode, languagecode)
        translationproject = self.getproject(languagecode, projectcode)
        translationproject.stats = {}
        for pofilename in translationproject.pofilenames:
          translationproject.getpostats(pofilename)
          translationproject.pofiles[pofilename] = pootlefile(translationproject, pofilename)
          print ".",
        print
        self.projectcache = {}

