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
    super(PootleServer, self).__init__(instance, sessioncache, errorhandler, loginpageclass)
    self.potree = projects.POTree(self.instance)
    for languagecode, language in self.potree.languages.iteritems():
      if not hasattr(language, "fullname"):
        language.fullname = languagecode
      for projectcode, project in language.projects.iteritems():
        if not hasattr(project, "fullname"):
          project.fullname = projectcode

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
    elif hasattr(self.potree.languages, top):
      language = getattr(self.potree.languages, top)
      pathwords = pathwords[1:]
      if pathwords:
        top = pathwords[0]
	bottom = pathwords[-1]
      else:
        top = ""
	bottom = ""
      if not top or top == "index.html":
        return indexpage.LanguageIndex(language, session)
      if hasattr(language.projects, top):
        project = getattr(language.projects, top)
	translationproject = projects.getproject(project)
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
          return translatepage.TranslatePage(language, project, session, argdict, dirfilter)
	elif bottom.endswith(".po"):
	  pofilename = os.path.join(*pathwords)
	  if argdict.get("translate", 0):
            return translatepage.TranslatePage(language, project, session, argdict, dirfilter=pofilename)
	  elif argdict.get("index", 0):
            return indexpage.ProjectIndex(project, session, argdict, dirfilter=pofilename)
	  else:
	    contents = translationproject.getsource(pofilename)
	    page = widgets.PlainContents(contents)
	    page.content_type = "text/plain"
	    return page
	elif bottom.endswith(".csv"):
	  csvfilename = os.path.join(*pathwords)
	  contents = translationproject.getcsv(csvfilename)
	  page = widgets.PlainContents(contents)
	  page.content_type = "text/plain"
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

if __name__ == '__main__':
  # run the web server
  from jToolkit.web import simplewebserver
  parser = simplewebserver.WebOptionParser()
  pootledir = os.path.abspath(os.path.dirname(__file__))
  prefsfile = os.path.join(pootledir, "pootle.prefs")
  parser.set_default('prefsfile', prefsfile)
  parser.set_default('instance', 'Pootle')
  htmldir = os.path.join(os.path.dirname(pootledir), "html")
  parser.set_default('htmldir', htmldir)
  options, args = parser.parse_args()
  server = parser.getserver(options)
  simplewebserver.run(server, options)

