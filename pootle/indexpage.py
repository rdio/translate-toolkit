#!/usr/bin/env python

from jToolkit.widgets import widgets
from translate.pootle import pagelayout

class PootleIndex(pagelayout.PootlePage):
  """the main page"""
  def __init__(self, session):
    self.instance = session.instance
    introtext = widgets.Division("<strong>Pootle</strong> is a simple web portal that should allow you to <strong>translate</strong>!", None, {"class":"intro"})
    nametext = widgets.Division('The name stands for <b>PO</b>-based <b>O</b>nline <b>T</b>ranslation / <b>L</b>ocalization <b>E</b>ngine, but you may need to read <a href="http://www.thechestnut.com/flumps.htm">this</a>.', None, {"class":"intro"})
    projectlinks = self.getprojectlinks()
    contents = widgets.Division([introtext, nametext, projectlinks], "content")
    pagelayout.PootlePage.__init__(self, "Pootle", contents, session)

  def getprojectlinks(self):
    """gets the links to the projects"""
    projectitems = [self.getprojectitem(projectcode, project) for projectcode, project in self.instance.projects.iteritems()]
    return widgets.Division(projectitems, None, {"class":"blog"})

  def getprojectitem(self, projectcode, project):
    bodytitle = '<h3 class="title">%s</h3>' % project.fullname
    bodydescription = widgets.Division('<a href="%s/">%s projects</a>' % (projectcode, project.fullname), None, {"class":"item-description"})
    body = widgets.Division([bodytitle, bodydescription], None, {"class":"blogbody"})
    subprojects = [subproject for (subprojectcode, subproject) in project.subprojects.iteritems()]
    subprojectcount = len(subprojects)
    percentfinished = 0
    stats = widgets.Division("%d subprojects, %d%% translated" % (subprojectcount, percentfinished), None, {"class":"posted"})
    return widgets.Division([body, stats], None, {"class":"item"})

class ProjectIndex(pagelayout.PootlePage):
  """the main page"""
  def __init__(self, project, session):
    self.project = project
    self.instance = session.instance
    subprojectlinks = self.getsubprojectlinks()
    contents = widgets.Division([subprojectlinks], "content")
    pagelayout.PootlePage.__init__(self, "Pootle: "+self.project.fullname, contents, session)

  def getsubprojectlinks(self):
    """gets the links to the projects"""
    subprojectitems = [self.getsubprojectitem(subprojectcode, subproject) for subprojectcode, subproject in self.project.subprojects.iteritems()]
    return widgets.Division(subprojectitems, None, {"class":"blog"})

  def getsubprojectitem(self, subprojectcode, subproject):
    bodytitle = '<h3 class="title">%s</h3>' % subproject.fullname
    bodydescription = widgets.Division('<a href="%s/">%s subproject</a>' % (subprojectcode, subproject.fullname), None, {"class":"item-description"})
    body = widgets.Division([bodytitle, bodydescription], None, {"class":"blogbody"})
    percentfinished = 0
    stats = widgets.Division("%d%% translated" % (percentfinished), None, {"class":"posted"})
    return widgets.Division([body, stats], None, {"class":"item"})

