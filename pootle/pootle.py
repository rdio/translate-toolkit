#!/usr/bin/env python

from jToolkit.web import server
from jToolkit.web import session
from jToolkit import prefs
from jToolkit.widgets import widgets
from translate.pootle import indexpage
from translate.pootle import translatepage
from translate.pootle import pagelayout
from translate.pootle import projects
from translate.pootle import users
import sys
import os
import random

class PootleServer(users.OptionalLoginAppServer):
  """the Server that serves the Pootle Pages"""
  def __init__(self, instance, sessioncache=None, errorhandler=None, loginpageclass=users.LoginPage):
    if sessioncache is None:
      sessioncache = session.SessionCache(sessionclass=users.PootleSession)
    self.localedomains = ["jToolkit", "pootle"]
    super(PootleServer, self).__init__(instance, sessioncache, errorhandler, loginpageclass)
    self.setdefaultoptions()
    self.potree = projects.POTree(self.instance)

  def saveprefs(self):
    """saves any changes made to the preferences"""
    # TODO: this is a hack, fix it up nicely :-)
    prefsfile = self.instance.__root__.__dict__["_setvalue"].im_self
    prefsfile.savefile()

  def setdefaultoptions(self):
    """sets the default options in the preferences"""
    changed = False
    if not hasattr(self.instance, "title"):
      setattr(self.instance, "title", "Pootle Demo")
      changed = True
    if not hasattr(self.instance, "description"):
      defaultdescription = "This is a demo installation of pootle. The administrator can customize the description in the preferences."
      setattr(self.instance, "description", defaultdescription)
      changed = True
    if not hasattr(self.instance, "baseurl"):
      setattr(self.instance, "baseurl", "/")
      changed = True
    if changed:
      self.saveprefs()

  def changeoptions(self, argdict):
    """changes options on the instance"""
    for key, value in argdict.iteritems():
      if not key.startswith("option-"):
        continue
      optionname = key.replace("option-", "", 1)
      setattr(self.instance, optionname, value)
    self.saveprefs()

  def refreshstats(self):
    """refreshes all the available statistics..."""
    self.potree.refreshstats()

  def generateactivationcode(self):
    """generates a unique activation code"""
    return "".join(["%02x" % int(random.random()*0x100) for i in range(16)])

  def getpage(self, pathwords, session, argdict):
    """return a page that will be sent to the user"""
    # TODO: strip off the initial path properly
    while pathwords and pathwords[0] == "pootle":
      pathwords = pathwords[1:]
    if pathwords:
      top = pathwords[0]
    else:
      top = ""
    if not top or top == "index.html":
      return indexpage.PootleIndex(self.potree, session)
    elif top == 'about.html':
      return indexpage.AboutPage(session)
    elif top == "login.html":
      if session.isopen:
        redirecttext = pagelayout.IntroText("Redirecting to home page...")
        redirectpage = pagelayout.PootlePage("Redirecting to home page...", redirecttext, session)
        return server.Redirect("home/", withpage=redirectpage)
      if 'username' in argdict:
        session.username = argdict["username"]
      return users.LoginPage(session, languagenames=self.languagenames)
    elif top == "register.html":
      return self.registerpage(session, argdict)
    elif top == "activate.html":
      return self.activatepage(session, argdict)
    elif top == "projects":
      pathwords = pathwords[1:]
      if pathwords:
        top = pathwords[0]
      else:
        top = ""
      if not top or top == "index.html":
        return indexpage.ProjectsIndex(self.potree, session)
      else:
        projectcode = top
        if not self.potree.hasproject(None, projectcode):
          return None
        pathwords = pathwords[1:]
        if pathwords:
          top = pathwords[0]
        else:
          top = ""
        if not top or top == "index.html":
          return indexpage.ProjectLanguageIndex(self.potree, projectcode, session)
    elif top == "home":
      pathwords = pathwords[1:]
      if pathwords:
        top = pathwords[0]
      else:
        top = ""
      if not session.isopen:
        redirecttext = pagelayout.IntroText("Redirecting to login...")
        redirectpage = pagelayout.PootlePage("Redirecting to login...", redirecttext, session)
        return server.Redirect("../login.html", withpage=redirectpage)
      if not top or top == "index.html":
        return indexpage.UserIndex(self.potree, session)
      elif top == "options.html":
        if "changeoptions" in argdict:
          session.setoptions(argdict)
        return indexpage.UserOptions(self.potree, session)
    elif top == "admin":
      pathwords = pathwords[1:]
      if pathwords:
        top = pathwords[0]
      else:
        top = ""
      if not session.isopen:
        redirecttext = pagelayout.IntroText("Redirecting to login...")
        redirectpage = pagelayout.PootlePage("Redirecting to login...", redirecttext, session)
        return server.Redirect("../login.html", withpage=redirectpage)
      if not session.issiteadmin():
        redirecttext = pagelayout.IntroText(self.localize("You do not have the rights to administer pootle."))
        redirectpage = pagelayout.PootlePage("Redirecting to home...", redirecttext, session)
        return server.Redirect("../index.html", withpage=redirectpage)
      if not top or top == "index.html":
        if "changegeneral" in argdict:
          self.changeoptions(argdict)
        if "changelanguages" in argdict:
          self.potree.changelanguages(argdict)
        if "changeprojects" in argdict:
          self.potree.changeprojects(argdict)
        return indexpage.AdminPage(self.potree, session, self.instance)
    elif self.potree.haslanguage(top):
      languagecode = top
      pathwords = pathwords[1:]
      if pathwords:
        top = pathwords[0]
	bottom = pathwords[-1]
      else:
        top = ""
	bottom = ""
      if not top or top == "index.html":
        return indexpage.LanguageIndex(self.potree, languagecode, session)
      if self.potree.hasproject(languagecode, top):
        projectcode = top
        project = self.potree.getproject(languagecode, projectcode)
        pathwords = pathwords[1:]
        if pathwords:
          top = pathwords[0]
        else:
          top = ""
        if not top or top == "index.html":
	  return indexpage.ProjectIndex(project, session, argdict)
	elif bottom == "translate.html":
	  if len(pathwords) > 1:
            dirfilter = os.path.join(*pathwords[:-1])
	  else:
	    dirfilter = ""
          try:
            return translatepage.TranslatePage(project, session, argdict, dirfilter)
          except (StopIteration, projects.RightsError), stoppedby:
            argdict["message"] = str(stoppedby)
            return indexpage.ProjectIndex(project, session, argdict, dirfilter)
	elif bottom.endswith(".po"):
	  pofilename = os.path.join(*pathwords)
	  if argdict.get("translate", 0):
            try:
              return translatepage.TranslatePage(project, session, argdict, dirfilter=pofilename)
            except (StopIteration, projects.RightsError), stoppedby:
              argdict["message"] = str(stoppedby)
              return indexpage.ProjectIndex(project, session, argdict, dirfilter=pofilename)
	  elif argdict.get("index", 0):
            return indexpage.ProjectIndex(project, session, argdict, dirfilter=pofilename)
	  else:
	    contents = project.getsource(pofilename)
	    page = widgets.PlainContents(contents)
	    page.content_type = "text/plain"
	    return page
	elif bottom.endswith(".csv"):
	  csvfilename = os.path.join(*pathwords)
	  contents = project.getcsv(csvfilename)
	  page = widgets.PlainContents(contents)
	  page.content_type = "text/plain"
	  return page
        elif bottom.endswith(".zip"):
	  if len(pathwords) > 1:
            dirfilter = os.path.join(*pathwords[:-1])
	  else:
	    dirfilter = None
          pofilenames = project.browsefiles(dirfilter)
          archivecontents = project.getarchive(pofilenames)
          page = widgets.PlainContents(archivecontents)
          page.content_type = "application/zip"
          return page
	elif bottom == "index.html":
          if len(pathwords) > 1:
            dirfilter = os.path.join(*pathwords[:-1])
          else:
            dirfilter = None
	  return indexpage.ProjectIndex(project, session, argdict, dirfilter)
	else:
	  return indexpage.ProjectIndex(project, session, argdict, os.path.join(*pathwords))
    return None

def main_is_frozen():
  import imp
  return (hasattr(sys, "frozen") or # new py2exe
          hasattr(sys, "importers") # old py2exe
          or imp.is_frozen("__main__")) # tools/freeze

def main():
  # run the web server
  from jToolkit.web import simplewebserver
  parser = simplewebserver.WebOptionParser()
  if main_is_frozen():
    pootledir = os.path.dirname(sys.executable)
  else:
    pootledir = os.path.abspath(os.path.dirname(__file__))
  prefsfile = os.path.join(pootledir, "pootle.prefs")
  parser.set_default('prefsfile', prefsfile)
  parser.set_default('instance', 'Pootle')
  htmldir = os.path.join(pootledir, "html")
  parser.set_default('htmldir', htmldir)
  parser.add_option('', "--refreshstats", dest="action", action="store_const", const="refreshstats", default="runwebserver", help="refresh the stats files instead of running the webserver")
  options, args = parser.parse_args()
  server = parser.getserver(options)
  if options.action == "runwebserver":
    simplewebserver.run(server, options)
  elif options.action == "refreshstats":
    server.refreshstats()

if __name__ == '__main__':
  main()

