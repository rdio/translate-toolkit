#!/usr/bin/env python

from jToolkit.widgets import widgets
from translate.pootle import pagelayout
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
    self.localize = session.localize
    introtext = pagelayout.IntroText(self.localize("<strong>Pootle</strong> is a simple web portal that should allow you to <strong>translate</strong>!"))
    nametext = pagelayout.IntroText(self.localize('The name stands for <b>PO</b>-based <b>O</b>nline <b>T</b>ranslation / <b>L</b>ocalization <b>E</b>ngine, but you may need to read <a href="http://www.thechestnut.com/flumps.htm">this</a>.'))
    languagelinks = self.getlanguagelinks()
    projectlinks = self.getprojectlinks()
    contents = [introtext, nametext, languagelinks, projectlinks]
    pagelayout.PootlePage.__init__(self, self.localize("Pootle"), contents, session)

  def getlanguagelinks(self):
    """gets the links to the languages"""
    languagestitle = self.localize('<h3 class="title">Languages</h3>')
    languagelinks = []
    for languagecode in self.potree.getlanguagecodes():
      languagename = self.potree.getlanguagename(languagecode)
      languagelink = widgets.Link(languagecode+"/", languagename)
      languagelinks.append(languagelink)
    listwidget = widgets.SeparatedList(languagelinks, ", ")
    bodydescription = pagelayout.ItemDescription(listwidget)
    return pagelayout.Contents([languagestitle, bodydescription])

  def getprojectlinks(self):
    """gets the links to the projects"""
    projectstitle = widgets.ContentWidget('h3', widgets.Link("projects/", self.localize("Projects")), {"class":"title"})
    projectlinks = []
    for projectcode in self.potree.getprojectcodes():
      projectname = self.potree.getprojectname(projectcode)
      projectdescription = self.potree.getprojectdescription(projectcode)
      projectlink = widgets.Link("projects/%s/" % projectcode, projectname, {"title":projectdescription})
      projectlinks.append(projectlink)
    listwidget = widgets.SeparatedList(projectlinks, ", ")
    bodydescription = pagelayout.ItemDescription(listwidget)
    return pagelayout.Contents([projectstitle, bodydescription])

class UserIndex(pagelayout.PootlePage):
  def __init__(self, potree, session):
    self.potree = potree
    self.session = session
    self.localize = session.localize
    submitbutton = widgets.Input({"type":"submit", "name":"changeoptions", "value":"Submit"})
    useroptions = widgets.Form([self.getprojectoptions(), submitbutton], {"name": "useroptions", "action":""})
    contents = [useroptions]
    pagelayout.PootlePage.__init__(self, self.localize("User Page for: %s") % session.username, contents, session)

  def getprojectoptions(self):
    """gets the links to the projects"""
    projectstitle = widgets.ContentWidget('h3', self.localize("My Projects"), {"class":"title"})
    projectoptions = []
    userprojects = self.session.getprojects()
    for projectcode in self.potree.getprojectcodes():
      projectname = self.potree.getprojectname(projectcode)
      projectoptions.append((projectcode, projectname))
      projectdescription = self.potree.getprojectdescription(projectcode)
    projectselect = widgets.MultiSelect({"value": userprojects, "name": "projects"}, projectoptions)
    bodydescription = pagelayout.ItemDescription([projectselect, widgets.HiddenFieldList({"allowmultikey":"projects"})])
    return pagelayout.Contents([projectstitle, bodydescription])

class ProjectsIndex(PootleIndex):
  """the list of projects"""
  def getlanguagelinks(self):
    """we don't need language links on the project page"""
    return ""

  def getprojectlinks(self):
    """gets the links to the projects"""
    projectstitle = self.localize('<h3 class="title">Projects</h3>')
    projectlinks = []
    for projectcode in self.potree.getprojectcodes():
      projectname = self.potree.getprojectname(projectcode)
      projectdescription = self.potree.getprojectdescription(projectcode)
      projectlink = widgets.Link("%s/" % projectcode, projectname, {"title":projectdescription})
      projectlinks.append(projectlink)
    listwidget = widgets.SeparatedList(projectlinks, ", ")
    bodydescription = pagelayout.ItemDescription(listwidget)
    return pagelayout.Contents([projectstitle, bodydescription])

class LanguageIndex(pagelayout.PootlePage):
  """the main page"""
  def __init__(self, potree, languagecode, session):
    self.potree = potree
    self.languagecode = languagecode
    self.localize = session.localize
    languagename = self.potree.getlanguagename(self.languagecode)
    projectlinks = self.getprojectlinks()
    pagelayout.PootlePage.__init__(self, "Pootle: "+languagename, projectlinks, session, bannerheight=81)

  def getprojectlinks(self):
    """gets the links to the projects"""
    projectcodes = self.potree.getprojectcodes(self.languagecode)
    projectitems = [self.getprojectitem(projectcode) for projectcode in projectcodes]
    return pagelayout.Contents(projectitems)

  def getprojectitem(self, projectcode):
    projectname = self.potree.getprojectname(projectcode)
    bodytitle = '<h3 class="title">%s</h3>' % projectname
    projectdescription = self.potree.getprojectdescription(projectcode)
    bodydescription = pagelayout.ItemDescription(widgets.Link(projectcode+"/", self.localize('%s project') % projectname, {"title":projectdescription}))
    body = pagelayout.ContentsItem([bodytitle, bodydescription])
    project = self.potree.getproject(self.languagecode, projectcode)
    numfiles = len(project.pofilenames)
    projectstats = project.calculatestats()
    translated = projectstats.get("translated", 0)
    total = projectstats.get("total", 0)
    percentfinished = (translated*100/max(total, 1))
    stats = pagelayout.ItemStatistics(self.localize("%d files, %d/%d strings (%d%%) translated") % (numfiles, translated, total, percentfinished))
    return pagelayout.Item([body, stats])

class ProjectLanguageIndex(pagelayout.PootlePage):
  """list of languages belonging to a project"""
  def __init__(self, potree, projectcode, session):
    self.potree = potree
    self.projectcode = projectcode
    self.localize = session.localize
    projectname = self.potree.getprojectname(self.projectcode)
    languagelinks = self.getlanguagelinks()
    pagelayout.PootlePage.__init__(self, "Pootle: "+projectname, languagelinks, session, bannerheight=81)

  def getlanguagelinks(self):
    """gets the links to the languages"""
    languagecodes = self.potree.getlanguagecodes(self.projectcode)
    languageitems = [self.getlanguageitem(languagecode) for languagecode in languagecodes]
    return pagelayout.Contents(languageitems)

  def getlanguageitem(self, languagecode):
    languagename = self.potree.getlanguagename(languagecode)
    bodytitle = '<h3 class="title">%s</h3>' % languagename
    bodydescription = pagelayout.ItemDescription(widgets.Link("../../%s/%s/" % (languagecode, self.projectcode), self.localize('%s language') % languagename))
    body = pagelayout.ContentsItem([bodytitle, bodydescription])
    language = self.potree.getproject(languagecode, self.projectcode)
    numfiles = len(language.pofilenames)
    languagestats = language.calculatestats()
    translated = languagestats.get("translated", 0)
    total = languagestats.get("total", 0)
    percentfinished = (translated*100/max(total, 1))
    stats = pagelayout.ItemStatistics(self.localize("%d files, %d/%d strings (%d%%) translated") % (numfiles, translated, total, percentfinished))
    return pagelayout.Item([body, stats])

class ProjectIndex(pagelayout.PootlePage):
  """the main page"""
  def __init__(self, project, session, argdict, dirfilter=None):
    self.project = project
    self.session = self.project.gettranslationsession(session)
    self.localize = session.localize
    self.rights = self.session.getrights()
    self.showchecks = argdict.get("showchecks", 0)
    if isinstance(self.showchecks, (str, unicode)) and self.showchecks.isdigit():
      self.showchecks = int(self.showchecks)
    message = argdict.get("message", "")
    if message:
      message = pagelayout.IntroText(message)
    bodytitle = '<h2 class="title">%s</h3>' % (dirfilter or self.project.projectname)
    bodytitle = widgets.Link(self.getbrowseurl(""), bodytitle)
    if dirfilter == "":
      dirfilter = None
    if dirfilter and dirfilter.endswith(".po"):
      actionlinks = []
      mainstats = []
      mainicon = pagelayout.Icon("file.png")
    else:
      pofilenames = self.project.browsefiles(dirfilter)
      projectstats = self.project.calculatestats(pofilenames)
      actionlinks = self.getactionlinks("", projectstats, ["review", "check", "quick", "all"])
      actionlinks = pagelayout.ActionLinks(actionlinks)
      mainstats = self.getitemstats("", projectstats, len(pofilenames))
      mainicon = pagelayout.Icon("folder.png")
    mainitem = pagelayout.MainItem([mainicon, bodytitle, actionlinks, mainstats])
    childitems = self.getchilditems(dirfilter)
    pagelayout.PootlePage.__init__(self, "Pootle: "+self.project.projectname, [message, mainitem, childitems], session, bannerheight=81)
    self.addsearchbox(searchtext="", action="translate.html")
    self.addnavlinks(dirfilter)

  def addnavlinks(self, dirfilter):
    """add navigation links to the sidebar"""
    if dirfilter and dirfilter.endswith(".po"):
      currentfolder = "/".join(dirfilter.split("/")[:-1])
    else:
      currentfolder = dirfilter
    if currentfolder:
      depth = currentfolder.count("/") + 1
      rootlink = "/".join([".."] * depth) + "/index.html"
    else:
      rootlink = "index.html"
    roottext = self.localize("%s (%s)") % (self.project.projectname, self.project.languagename)
    self.addfolderlinks(self.localize("project root"), roottext, rootlink, self.project.projectdescription)
    self.addfolderlinks(self.localize("current folder"), currentfolder, "index.html")
    if dirfilter is not None:
      parentfolder = "/".join(currentfolder.split("/")[:-1])
      if parentfolder:
        self.addfolderlinks(self.localize("parent folder"), parentfolder, "../index.html")
    if currentfolder:
      archivename = "%s-%s-%s.zip" % (self.project.projectcode, self.project.languagecode, currentfolder.replace("/", "-"))
    else:
      archivename = "%s-%s.zip" % (self.project.projectcode, self.project.languagecode)
    self.addfolderlinks(self.localize("zip of folder"), archivename, archivename)

  def getchilditems(self, dirfilter):
    """get all the items for directories and files viewable at this level"""
    if dirfilter is None:
      depth = 0
    else:
      depth = dirfilter.count(os.path.sep)
      if not dirfilter.endswith(os.path.extsep + "po"):
        depth += 1
    diritems = []
    for childdir in self.project.browsefiles(dirfilter=dirfilter, depth=depth, includedirs=True, includefiles=False):
      diritem = self.getdiritem(childdir)
      diritems.append((childdir, diritem))
    diritems.sort()
    fileitems = []
    for childfile in self.project.browsefiles(dirfilter=dirfilter, depth=depth, includefiles=True, includedirs=False):
      fileitem = self.getfileitem(childfile)
      fileitems.append((childfile, fileitem))
    fileitems.sort()
    childitems = [diritem for childdir, diritem in diritems] + [fileitem for childfile, fileitem in fileitems]
    polarity = False
    for childitem in childitems:
      childitem.setpolarity(polarity)
      polarity = not polarity
    return childitems

  def getdiritem(self, direntry):
    """returns an item showing a directory entry"""
    pofilenames = self.project.browsefiles(direntry)
    projectstats = self.project.calculatestats(pofilenames)
    basename = os.path.basename(direntry)
    bodytitle = '<h3 class="title">%s</h3>' % basename
    basename += "/"
    folderimage = pagelayout.Icon("folder.png")
    browseurl = self.getbrowseurl(basename)
    bodytitle = widgets.Link(browseurl, bodytitle)
    actionlinks = self.getactionlinks(basename, projectstats)
    bodydescription = pagelayout.ActionLinks(actionlinks)
    body = pagelayout.ContentsItem([folderimage, bodytitle, bodydescription])
    stats = self.getitemstats(basename, projectstats, len(pofilenames))
    return pagelayout.Item([body, stats])

  def getfileitem(self, fileentry):
    """returns an item showing a file entry"""
    basename = os.path.basename(fileentry)
    projectstats = self.project.calculatestats([fileentry])
    folderimage = pagelayout.Icon("file.png")
    browseurl = self.getbrowseurl(basename)
    bodytitle = widgets.Link(browseurl, '<h3 class="title">%s</h3>' % basename)
    actionlinks = self.getactionlinks(basename, projectstats)
    downloadlink = widgets.Link(basename, self.localize('PO file'))
    csvname = basename.replace(".po", ".csv")
    csvlink = widgets.Link(csvname, self.localize('CSV file'))
    bodydescription = pagelayout.ActionLinks(actionlinks + [downloadlink, csvlink])
    body = pagelayout.ContentsItem([folderimage, bodytitle, bodydescription])
    stats = self.getitemstats(basename, projectstats, None)
    return pagelayout.Item([body, stats])

  def getbrowseurl(self, basename):
    """gets the link to browse the item"""
    if not basename or basename.endswith("/"):
      return basename or "index.html"
    else:
      baseactionlink = "%s?translate=1" % basename
      return '%s&view=1' % baseactionlink

  def getactionlinks(self, basename, projectstats, linksrequired=None):
    """get links to the actions that can be taken on an item (directory / file)"""
    if linksrequired is None:
      linksrequired = ["review", "quick", "all"]
    actionlinks = []
    if not basename or basename.endswith("/"):
      baseactionlink = basename + "translate.html?"
      baseindexlink = basename + "index.html?"
    else:
      baseactionlink = "%s?translate=1" % basename
      baseindexlink = "%s?index=1" % basename
    if "check" in linksrequired and "translate" in self.rights:
      if self.showchecks:
        checkslink = widgets.Link(baseindexlink + "&showchecks=0", self.localize("Hide Checks"))
      else:
        checkslink = widgets.Link(baseindexlink + "&showchecks=1", self.localize("Show Checks"))
      actionlinks.append(checkslink)
    if "review" in linksrequired and projectstats.get("has-suggestion", 0):
      if "review" in self.rights:
        reviewlink = self.localize("Review Suggestions")
      else:
        reviewlink = self.localize("View Suggestions")
      reviewlink = widgets.Link(baseactionlink + "&review=1&has-suggestion=1", reviewlink)
      actionlinks.append(reviewlink)
    if "quick" in linksrequired and projectstats.get("translated", 0) < projectstats.get("total", 0):
      if "translate" in self.rights:
        quicklink = self.localize("Quick Translate")
      else:
        quicklink = self.localize("View Untranslated")
      quicklink = widgets.Link(baseactionlink + "&fuzzy=1&blank=1", quicklink)
      actionlinks.append(quicklink)
    if "all" in linksrequired and "translate" in self.rights:
      translatelink = widgets.Link(baseactionlink, self.localize('Translate All'))
      actionlinks.append(translatelink)
    return actionlinks

  def getitemstats(self, basename, projectstats, numfiles):
    """returns a widget summarizing item statistics"""
    translated = projectstats.get("translated", 0)
    total = projectstats.get("total", 0)
    percentfinished = (translated*100/max(total, 1))
    statssummary = self.localize("%d/%d strings (%d%%) translated") % (translated, total, percentfinished)
    if numfiles is not None:
      statssummary = (self.localize("%d files, ") % numfiles) + statssummary
    if total and self.showchecks:
      if not basename or basename.endswith("/"):
        checklinkbase = basename + "translate.html?"
      else:
        checklinkbase = basename + "?translate=1"
      statsdetails = "<br/>\n".join(self.getcheckdetails(projectstats, checklinkbase))
      statssummary += "<br/>" + statsdetails
    return pagelayout.ItemStatistics(statssummary)

  def getcheckdetails(self, projectstats, checklinkbase):
    """return a list of strings describing the results of checks"""
    total = max(projectstats.get("total", 0), 1)
    for checkname, checkcount in projectstats.iteritems():
      if not checkname.startswith("check-"):
        continue
      checkname = checkname.replace("check-", "", 1)
      if total and checkcount:
        checklink = "<a href='%s&%s=1'>%s</a>" % (checklinkbase, checkname, checkname)
        stats = self.localize("%d strings (%d%%) failed") % (checkcount, (checkcount * 100 / total))
        yield "%s: %s" % (checklink, stats)

