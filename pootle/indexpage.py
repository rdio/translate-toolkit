#!/usr/bin/env python

from jToolkit.widgets import widgets
from translate.pootle import pagelayout
from translate.pootle import projects
import os

def summarizestats(statslist, totalstats=None):
  if totalstats is None:
    totalstats = {}
  for statsdict in statslist:
    for name, count in statsdict.iteritems():
      totalstats[name] = totalstats.get(name, 0) + count
  return totalstats

class PootleIndex(pagelayout.PootlePage):
  """the main page"""
  def __init__(self, potree, session):
    self.potree = potree
    introtext = pagelayout.IntroText("<strong>Pootle</strong> is a simple web portal that should allow you to <strong>translate</strong>!")
    nametext = pagelayout.IntroText('The name stands for <b>PO</b>-based <b>O</b>nline <b>T</b>ranslation / <b>L</b>ocalization <b>E</b>ngine, but you may need to read <a href="http://www.thechestnut.com/flumps.htm">this</a>.')
    languagelinks = self.getlanguagelinks()
    contents = [introtext, nametext, languagelinks]
    pagelayout.PootlePage.__init__(self, "Pootle", contents, session)

  def getlanguagelinks(self):
    """gets the links to the languages"""
    languageitems = [self.getlanguageitem(languagecode) for languagecode in self.potree.getlanguagecodes()]
    return pagelayout.Contents(languageitems)

  def getlanguageitem(self, languagecode):
    languagename = self.potree.getlanguagename(languagecode)
    bodytitle = '<h3 class="title">%s</h3>' % languagename
    bodydescription = pagelayout.ItemDescription(widgets.Link(languagecode+"/", languagename))
    body = pagelayout.ContentsItem([bodytitle, bodydescription])
    projectcodes = self.potree.getprojectcodes(languagecode)
    projectlist = [self.potree.getproject(languagecode, projectcode) for projectcode in projectcodes]
    projectcount = len(projectlist)
    projectstats = [project.calculatestats() for project in projectlist]
    totalstats = summarizestats(projectstats, {"translated":0, "total":0})
    translated = totalstats["translated"]
    total = totalstats["total"]
    percentfinished = (translated*100/max(total, 1))
    stats = pagelayout.ItemStatistics("%d projects, %d%% translated" % (projectcount, percentfinished))
    return pagelayout.Item([body, stats])

class LanguageIndex(pagelayout.PootlePage):
  """the main page"""
  def __init__(self, potree, languagecode, session):
    self.potree = potree
    self.languagecode = languagecode
    languagename = self.potree.getlanguagename(self.languagecode)
    projectlinks = self.getprojectlinks()
    pagelayout.PootlePage.__init__(self, "Pootle: "+languagename, projectlinks, session, bannerheight=81)

  def getprojectlinks(self):
    """gets the links to the projects"""
    projectcodes = self.potree.getprojectcodes(self.languagecode)
    projectitems = [self.getprojectitem(projectcode) for projectcode in projectcodes]
    return pagelayout.Contents(projectitems)

  def getprojectitem(self, projectcode):
    projectname = self.potree.getprojectname(self.languagecode, projectcode)
    bodytitle = '<h3 class="title">%s</h3>' % projectname
    bodydescription = pagelayout.ItemDescription(widgets.Link(projectcode+"/", '%s project' % projectname))
    body = pagelayout.ContentsItem([bodytitle, bodydescription])
    project = self.potree.getproject(self.languagecode, projectcode)
    numfiles = len(project.pofilenames)
    projectstats = project.calculatestats()
    translated = projectstats.get("translated", 0)
    total = projectstats.get("total", 0)
    percentfinished = (translated*100/max(total, 1))
    stats = pagelayout.ItemStatistics("%d files, %d/%d strings (%d%%) translated" % (numfiles, translated, total, percentfinished))
    return pagelayout.Item([body, stats])

class ProjectIndex(pagelayout.PootlePage):
  """the main page"""
  def __init__(self, project, session, argdict, dirfilter=None):
    self.project = project
    self.showchecks = argdict.get("showchecks", 0)
    if isinstance(self.showchecks, str) and self.showchecks.isdigit():
      self.showchecks = int(self.showchecks)
    browselink = widgets.Link("index.html", "Browse")
    checkslink = widgets.Link("index.html?showchecks=1", "Checks")
    quicklink = widgets.Link("translate.html?fuzzy=1&blank=1", "Quick Translate")
    message = argdict.get("message", [])
    if message:
      message = pagelayout.IntroText(message)
    processlinks = pagelayout.IntroText([browselink, checkslink, quicklink])
    if dirfilter is None:
      depth = 0
    else:
      depth = dirfilter.count(os.path.sep)
      if not dirfilter.endswith(os.path.extsep + "po"):
        depth += 1
    direntries = []
    fileentries = []
    for childdir in self.project.browsefiles(dirfilter=dirfilter, depth=depth, includedirs=True, includefiles=False):
      direntry = self.getdiritem(childdir)
      direntries.append(direntry)
    for childfile in self.project.browsefiles(dirfilter=dirfilter, depth=depth, includefiles=True, includedirs=False):
      fileentry = self.getfileitem(childfile)
      fileentries.append(fileentry)
    pagelayout.PootlePage.__init__(self, "Pootle: "+self.project.projectname, [message, processlinks, direntries, fileentries], session, bannerheight=81)

  def getdiritem(self, direntry):
    basename = os.path.basename(direntry)
    bodytitle = '<h3 class="title">%s</h3>' % basename
    browselink = widgets.Link(basename+"/", 'Browse')
    checkslink = widgets.Link("%s/index.html?showchecks=1" % basename, "Checks")
    quicklink = widgets.Link("%s/translate.html?fuzzy=1&blank=1" % basename, "Quick Translate")
    bodydescription = pagelayout.ItemDescription([browselink, checkslink, quicklink])
    body = pagelayout.ContentsItem([bodytitle, bodydescription])
    pofilenames = self.project.browsefiles(direntry)
    numfiles = len(pofilenames)
    projectstats = self.project.calculatestats(pofilenames)
    translated = projectstats.get("translated", 0)
    total = projectstats.get("total", 0)
    percentfinished = (translated*100/max(total, 1))
    statssummary = "%d files, %d/%d strings (%d%%) translated" % (numfiles, translated, total, percentfinished)
    if total and self.showchecks:
      statsdetails = "<br/>\n".join(self.getcheckdetails(projectstats, "%s/translate.html?" % basename))
      statssummary += "<br/>" + statsdetails
    stats = pagelayout.ItemStatistics(statssummary)
    return pagelayout.Item([body, stats])

  def getcheckdetails(self, projectstats, checklinkbase):
    """return a list of strings describing the results of checks"""
    total = max(projectstats.get("total", 0), 1)
    for checkname, checkcount in projectstats.iteritems():
      if not checkname.startswith("check-"):
        continue
      checkname = checkname.replace("check-", "", 1)
      if total and checkcount:
        checklink = "<a href='%s%s=1'>%s</a>" % (checklinkbase, checkname, checkname)
        stats = "%d strings (%d%%) failed" % (checkcount, (checkcount * 100 / total))
        yield "%s: %s" % (checklink, stats)

  def getfileitem(self, fileentry):
    basename = os.path.basename(fileentry)
    bodytitle = '<h3 class="title">%s</h3>' % basename
    browselink = widgets.Link('%s?translate=1' % basename, 'Browse')
    checkslink = widgets.Link("%s?index=1&showchecks=1" % basename, "Checks")
    quicklink = widgets.Link('%s?translate=1&fuzzy=1&blank=1' % basename, 'Quick Translate')
    downloadlink = widgets.Link(basename, 'PO file')
    csvname = basename.replace(".po", ".csv")
    csvlink = widgets.Link(csvname, 'CSV file')
    bodydescription = pagelayout.ItemDescription([browselink, checkslink, quicklink, downloadlink, csvlink])
    pofilenames = [fileentry]
    projectstats = self.project.calculatestats(pofilenames)
    translated = projectstats.get("translated", 0)
    total = projectstats.get("total", 0)
    percentfinished = (translated*100/max(total, 1))
    body = pagelayout.ContentsItem([bodytitle, bodydescription])
    statssummary = "%d/%d strings (%d%%) translated" % (translated, total, percentfinished)
    if total and self.showchecks:
      statsdetails = "<br/>\n".join(self.getcheckdetails(projectstats, '%s?translate=1&' % basename))
      statssummary += "<br/>" + statsdetails
    stats = pagelayout.ItemStatistics(statssummary)
    return pagelayout.Item([body, stats])

