#!/usr/bin/env python

from jToolkit.web import server
from jToolkit.web.session import md5hexdigest
from jToolkit import prefs
from jToolkit.widgets import widgets
from jToolkit.widgets import form
from jToolkit import mailer
from jToolkit import passwordgen
from translate.pootle import indexpage
from translate.pootle import translatepage
from translate.pootle import pagelayout
from translate.pootle import projects
import os

class LoginPage(server.LoginPage, pagelayout.PootlePage):
  """wraps the normal login page in a PootlePage layout"""
  def __init__(self, session, extraargs={}, confirmlogin=0, specialmessage=None, languagenames=None):
    server.LoginPage.__init__(self, session, extraargs, confirmlogin, specialmessage, languagenames)
    contents = pagelayout.IntroText(self.contents)
    pagelayout.PootlePage.__init__(self, "Login to Pootle", contents, session)

  def getcontents(self):
    return pagelayout.PootlePage.getcontents(self)

class RegisterPage(pagelayout.PootlePage):
  """page for new registrations"""
  def __init__(self, session):
    contents = self.getform()
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
    super(PootleServer, self).__init__(instance, sessioncache, errorhandler)
    for projectcode, project in self.instance.projects.iteritems():
      if not hasattr(project, "fullname"):
        project.fullname = projectcode
      for subprojectcode, subproject in project.subprojects.iteritems():
        if not hasattr(subproject, "fullname"):
          subproject.fullname = subprojectcode

  def saveprefs(self):
    """saves changed preferences back to disk"""
    # TODO: this is a hack, fix it up nicely :-)
    prefsfile = self.instance.__root__.__dict__["_setvalue"].im_self
    prefsfile.savefile()

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
        password = passwordgen.createpassword()
        userexists = session.userexists(username)
        if userexists:
	  getattr(self.instance.users, username).passwdhash = md5hexdigest(password)
          message = "your password has been updated\n"
        else:
	  setattr(self.instance.users, username + ".passwdhash", md5hexdigest(password))
          message = "an account has been created for you\n"
	self.saveprefs()
        message += "username: %s\npassword: %s\n" % (username, password)
        # TODO: handle emailing properly, but printing now to make it easier
	print message
        # mailer.dosendmessage(self.instance.registration.fromaddress, [username], message)
        redirecttext = pagelayout.IntroText(message + "Redirecting to login...")
        redirectpage = pagelayout.PootlePage("Redirecting to login...", redirecttext, session)
	redirectpage.attribs["refresh"] = 10
	redirectpage.attribs["refreshurl"] = "login.html"
        return redirectpage
      else:
        return RegisterPage(session)
    elif hasattr(session.instance.projects, top):
      project = getattr(session.instance.projects, top)
      pathwords = pathwords[1:]
      if pathwords:
        top = pathwords[0]
	bottom = pathwords[-1]
      else:
        top = ""
	bottom = ""
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
	  return indexpage.SubprojectIndex(subproject, session)
	elif bottom == "translate.html":
	  if len(pathwords) > 1:
            dirfilter = os.path.join(*pathwords[:-1])
	  else:
	    dirfilter = ""
          return translatepage.TranslatePage(project, subproject, session, argdict, dirfilter)
	elif bottom.endswith(".po"):
	  pofilename = os.path.join(*pathwords)
	  if argdict.get("translate", 0):
            return translatepage.TranslatePage(project, subproject, session, argdict, dirfilter=pofilename)
	  else:
	    translationproject = projects.getproject(subproject)
	    contents = translationproject.getsource(pofilename)
	    page = widgets.PlainContents(contents)
	    page.content_type = "text/plain"
	    return page
	elif bottom.endswith(".csv"):
	  csvfilename = os.path.join(*pathwords)
	  translationproject = projects.getproject(subproject)
	  contents = translationproject.getcsv(csvfilename)
	  page = widgets.PlainContents(contents)
	  page.content_type = "text/plain"
	  return page
	else:
	  return indexpage.SubprojectIndex(subproject, session, os.path.join(*pathwords))
    return None

