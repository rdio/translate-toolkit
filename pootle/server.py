#!/usr/bin/env python

from jToolkit.web import server
from jToolkit.widgets import widgets
from translate.pootle import indexpage
from translate.pootle import translatepage
from translate.pootle import pagelayout

class LoginPage(server.LoginPage, pagelayout.PootlePage):
  """wraps the normal login page in a PootlePage layout"""
  def __init__(self, session, extraargs={}, confirmlogin=0, specialmessage=None, languagenames=None):
    server.LoginPage.__init__(self, session, extraargs, confirmlogin, specialmessage, languagenames)
    loginform = self.contents
    contents = widgets.Division(widgets.Division(loginform, None, {"class":"intro"}), "content")
    pagelayout.PootlePage.__init__(self, "Login to Pootle", contents, session)

class OptionalLoginAppServer(server.LoginAppServer):
  """a server that enables login but doesn't require it except for specified pages"""
  def handle(self, req, pathwords, argdict):
    """handles the request and returns a page object in response"""
    argdict = self.processargs(argdict)
    session = self.getsession(req, argdict)
    if session.isopen:
      session.pagecount += 1
      session.remote_ip = self.getremoteip(req)
    return self.getpage(pathwords, session, argdict)

class PootleServer(OptionalLoginAppServer):
  """the Server that serves the Pootle Pages"""
  def __init__(self, instance, sessioncache=None, errorhandler=None, loginpageclass=LoginPage, cachetables=None):
    super(PootleServer, self).__init__(instance, sessioncache, errorhandler, loginpageclass, cachetables)

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
      return indexpage.PootleIndex(session)
    elif hasattr(session.instance.projects, top):
      project = getattr(session.instance.projects, top)
      pathwords = pathwords[1:]
      if pathwords:
        top = pathwords[0]
      else:
        top = ""
      if not top or top == "index.html":
        return indexpage.ProjectIndex(project, session)
      if hasattr(project.subprojects, top):
        subproject = getattr(project.subprojects, top)
        pathwords = pathwords[1:]
        if pathwords:
          top = pathwords[0]
        else:
          top = ""
        if not top or top == "index.html":
          return translatepage.TranslatePage(project, subproject, session, argdict)
    elif top == "test.html":
      contents = repr(session.status)
      page = widgets.PlainContents(contents)
      page.content_type = "text/plain"
      return page
    return None

