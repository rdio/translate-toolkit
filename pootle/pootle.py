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
  def __init__(self, session, argdict):
    introtext = [pagelayout.IntroText("Please enter your registration details"),
                 pagelayout.IntroText("Current Status: %s" % session.status)]
    self.argdict = argdict
    contents = [introtext, self.getform()]
    pagelayout.PootlePage.__init__(self, "Pootle Registration", contents, session)

  def getform(self):
    columnlist = [("email", "Email Address", "Must be a valid email address"),
                  ("username", "Username", "Your requested username")]
    formlayout = {1:("email", ), 2:("username", )}
    extrawidgets = [widgets.Input({'type': 'submit', 'name':'register', 'value':'Register'})]
    record = dict([(column[0], self.argdict.get(column[0], "")) for column in columnlist])
    return form.SimpleForm(record, "register", columnlist, formlayout, {}, extrawidgets)

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
  def __init__(self, instance, sessioncache=None, errorhandler=None, loginpageclass=LoginPage):
    super(PootleServer, self).__init__(instance, sessioncache, errorhandler, loginpageclass)
    self.potree = projects.POTree(self.instance)

  def saveprefs(self):
    """saves changed preferences back to disk"""
    # TODO: this is a hack, fix it up nicely :-)
    prefsfile = self.instance.__root__.__dict__["_setvalue"].im_self
    prefsfile.savefile()

  def refreshstats(self):
    """refreshes all the available statistics..."""
    self.potree.refreshstats()

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
    elif top == "login.html":
      if session.isopen:
        redirecttext = pagelayout.IntroText("Redirecting to index...")
        redirectpage = pagelayout.PootlePage("Redirecting to index...", redirecttext, session)
        return server.Redirect("index.html", withpage=redirectpage)
      return LoginPage(session)
    elif top == "register.html":
      return self.registerpage(session, argdict)
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
        pathwords = pathwords[1:]
        if pathwords:
          top = pathwords[0]
        else:
          top = ""
        if not top or top == "index.html":
          return indexpage.ProjectLanguageIndex(self.potree, projectcode, session)
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
          except StopIteration, stoppedby:
            argdict["message"] = str(stoppedby)
            return indexpage.ProjectIndex(project, session, argdict, dirfilter)
	elif bottom.endswith(".po"):
	  pofilename = os.path.join(*pathwords)
	  if argdict.get("translate", 0):
            try:
              return translatepage.TranslatePage(project, session, argdict, dirfilter=pofilename)
            except StopIteration, stoppedby:
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
	elif bottom == "index.html":
          if len(pathwords) > 1:
            dirfilter = os.path.join(*pathwords[:-1])
          else:
            dirfilter = None
	  return indexpage.ProjectIndex(project, session, argdict, dirfilter)
	else:
	  return indexpage.ProjectIndex(project, session, argdict, os.path.join(*pathwords))
    return None

  def handleregistration(self, session, argdict):
    """handles the actual registration"""
    username = argdict.get("username", "")
    if not username or not username.isalnum() or not username[0].isalpha():
      raise ValueError("username must be alphanumeric")
    email = argdict.get("email", "")
    if not email:
      raise ValueError("must supply a valid email address")
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
    return message

  def registerpage(self, session, argdict):
    """handle registration or return the Register page"""
    if "username" in argdict:
      try:
        message = self.handleregistration(session, argdict)
      except ValueError, message:
        session.status = str(message)
        return RegisterPage(session, argdict)
      # mailer.dosendmessage(self.instance.registration.fromaddress, [username], message)
      redirecttext = pagelayout.IntroText(message + "Redirecting to login...")
      redirectpage = pagelayout.PootlePage("Redirecting to login...", redirecttext, session)
      redirectpage.attribs["refresh"] = 10
      redirectpage.attribs["refreshurl"] = "login.html"
      return redirectpage
    else:
      return RegisterPage(session, argdict)

if __name__ == '__main__':
  # run the web server
  from jToolkit.web import simplewebserver
  parser = simplewebserver.WebOptionParser()
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


