#!/usr/bin/env python

from jToolkit.web import server
from jToolkit.web.session import md5hexdigest
from jToolkit.widgets import widgets
from jToolkit.widgets import form
from translate.pootle import indexpage
from translate.pootle import translatepage
from translate.pootle import pagelayout

class LoginPage(server.LoginPage, pagelayout.PootlePage):
  """wraps the normal login page in a PootlePage layout"""
  def __init__(self, session, extraargs={}, confirmlogin=0, specialmessage=None, languagenames=None):
    server.LoginPage.__init__(self, session, extraargs, confirmlogin, specialmessage, languagenames)
    loginform = self.contents
    contents = widgets.Division(pagelayout.IntroText(loginform), "content")
    pagelayout.PootlePage.__init__(self, "Login to Pootle", contents, session)

class RegisterPage(pagelayout.PootlePage):
  """page for new registrations"""
  def __init__(self, session):
    contents = widgets.Division(self.getform(), "content")
    pagelayout.PootlePage.__init__(self, "Pootle Registration", contents, session)

  def getform(self):
    columnlist = [("username", "Email Address", "Must be a valid email address")]
    formlayout = {1:("username", )}
    optionsdict = {}
    extrawidgets = [widgets.Input({'type': 'submit', 'name':'register', 'value':'Register'})]
    record = dict([(column[0], "") for column in columnlist])
    return form.SimpleForm(record, "register", columnlist, formlayout, optionsdict, extrawidgets)

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
    elif top == "login.html":
      if session.isopen:
        redirecttext = pagelayout.IntroText("Redirecting to index...")
        redirectpage = pagelayout.PootlePage("Redirecting to index...", redirecttext, session)
        return server.Redirect("index.html", withpage=redirectpage)
      return LoginPage(session)
    elif top == "register.html":
      if "username" in argdict:
        username = argdict["username"]
        session.db.insert("users", {"username":username, "passwdhash":md5hexdigest(username)})
        return LoginPage(session)
      else:
        return RegisterPage(session)
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

