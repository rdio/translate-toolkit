#!/usr/bin/env python

from jToolkit.widgets import widgets
from translate.pootle import pagelayout
from translate.pootle import projects

class PootleIndex(pagelayout.PootlePage):
  """the main page"""
  def __init__(self, session):
    self.instance = session.instance
    introtext = pagelayout.IntroText("<strong>Pootle</strong> is a simple web portal that should allow you to <strong>translate</strong>!")
    nametext = pagelayout.IntroText('The name stands for <b>PO</b>-based <b>O</b>nline <b>T</b>ranslation / <b>L</b>ocalization <b>E</b>ngine, but you may need to read <a href="http://www.thechestnut.com/flumps.htm">this</a>.')
    projectlinks = self.getprojectlinks()
    contents = [introtext, nametext, projectlinks]
    pagelayout.PootlePage.__init__(self, "Pootle", contents, session)

  def getprojectlinks(self):
    """gets the links to the projects"""
    projectitems = [self.getprojectitem(projectcode, project) for projectcode, project in self.instance.projects.iteritems()]
    return pagelayout.Contents(projectitems)

  def getprojectitem(self, projectcode, project):
    bodytitle = '<h3 class="title">%s</h3>' % project.fullname
    bodydescription = pagelayout.ItemDescription('<a href="%s/">%s projects</a>' % (projectcode, project.fullname))
    body = pagelayout.ContentsItem([bodytitle, bodydescription])
    subprojects = [projects.getproject(subproject) for (subprojectcode, subproject) in project.subprojects.iteritems()]
    subprojectcount = len(subprojects)
    totalstats = {"translated":0, "total":0}
    for subproject in subprojects:
      projectstats = subproject.calculatestats()
      for name, count in projectstats.iteritems():
        totalstats[name] = totalstats.get(name, 0) + count
    translated = totalstats["translated"]
    total = totalstats["total"]
    percentfinished = (translated*100/max(total, 1))
    stats = pagelayout.ItemStatistics("%d subprojects, %d%% translated" % (subprojectcount, percentfinished))
    return pagelayout.Item([body, stats])

class ProjectIndex(pagelayout.PootlePage):
  """the main page"""
  def __init__(self, project, session):
    self.project = project
    self.instance = session.instance
    subprojectlinks = self.getsubprojectlinks()
    pagelayout.PootlePage.__init__(self, "Pootle: "+self.project.fullname, subprojectlinks, session)

  def getsubprojectlinks(self):
    """gets the links to the projects"""
    subprojectitems = [self.getsubprojectitem(subprojectcode, subproject) for subprojectcode, subproject in self.project.subprojects.iteritems()]
    return pagelayout.Contents(subprojectitems)

  def getsubprojectitem(self, subprojectcode, subproject):
    bodytitle = '<h3 class="title">%s</h3>' % subproject.fullname
    bodydescription = pagelayout.ItemDescription('<a href="%s/">%s subproject</a>' % (subprojectcode, subproject.fullname))
    body = pagelayout.ContentsItem([bodytitle, bodydescription])
    translationproject = projects.getproject(subproject)
    numfiles = len(translationproject.pofilenames)
    projectstats = translationproject.calculatestats()
    translated = projectstats.get("translated", 0)
    total = projectstats.get("total", 0)
    percentfinished = (translated*100/max(total, 1))
    stats = pagelayout.ItemStatistics("%d files, %d/%d strings (%d%%) translated" % (numfiles, translated, total, percentfinished))
    return pagelayout.Item([body, stats])

