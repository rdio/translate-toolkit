#!/usr/bin/env python

from jToolkit.web import server
from jToolkit.web import session
from jToolkit import prefs
from jToolkit.widgets import widgets
from jToolkit.widgets import form
from jToolkit import mailer
from translate.pootle import indexpage
from translate.pootle import translatepage
from translate.pootle import pagelayout
from translate.pootle import projects
import sys
import os
import random

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
                  ("username", "Username", "Your requested username"),
                  ("password", "Password", "Your desired password")]
    formlayout = {1:("email", ), 2:("username", ), 3:("password", )}
    extrawidgets = [widgets.Input({'type': 'submit', 'name':'register', 'value':'Register'})]
    record = dict([(column[0], self.argdict.get(column[0], "")) for column in columnlist])
    return form.SimpleForm(record, "register", columnlist, formlayout, {}, extrawidgets)

class ActivatePage(pagelayout.PootlePage):
  """page for new registrations"""
  def __init__(self, session, argdict):
    introtext = [pagelayout.IntroText("Please enter your activation details"),
                 pagelayout.IntroText("Current Status: %s" % session.status)]
    self.argdict = argdict
    contents = [introtext, self.getform()]
    pagelayout.PootlePage.__init__(self, "Pootle Account Activation", contents, session)

  def getform(self):
    columnlist = [("username", "Username", "Your requested username"),
                  ("activationcode", "Activation Code", "The activation code you received")]
    formlayout = {1:("username", ), 2:("activationcode", )}
    extrawidgets = [widgets.Input({'type': 'submit', 'name':'activate', 'value':'Activate Account'})]
    record = dict([(column[0], self.argdict.get(column[0], "")) for column in columnlist])
    return form.SimpleForm(record, "activate", columnlist, formlayout, {}, extrawidgets)

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

class ActivateSession(session.LoginSession):
  # TODO: refactor this into a LoginChecker somehow...
  def validate(self):
    """checks if this session is valid"""
    if not super(ActivateSession, self).validate():
      return False
    if not getattr(getattr(self.loginchecker.users, self.username, None), "activated", 0):
      self.isvalid = False
      self.status = "username has not yet been activated"
    return self.isvalid

class PootleServer(OptionalLoginAppServer):
  """the Server that serves the Pootle Pages"""
  def __init__(self, instance, sessioncache=None, errorhandler=None, loginpageclass=LoginPage):
    if sessioncache is None:
      sessioncache = session.SessionCache(sessionclass=ActivateSession)
    super(PootleServer, self).__init__(instance, sessioncache, errorhandler, loginpageclass)
    self.potree = projects.POTree(self.instance)

  def saveuserprefs(self, users):
    """saves changed preferences back to disk"""
    # TODO: this is a hack, fix it up nicely :-)
    prefsfile = users.__root__.__dict__["_setvalue"].im_self
    prefsfile.savefile()

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
    elif top == "login.html":
      if session.isopen:
        redirecttext = pagelayout.IntroText("Redirecting to index...")
        redirectpage = pagelayout.PootlePage("Redirecting to index...", redirecttext, session)
        return server.Redirect("index.html", withpage=redirectpage)
      return LoginPage(session)
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
    password = argdict.get("password", "")
    if not email:
      raise ValueError("must supply a valid email address")
    minpasswordlen = 6
    if not password or len(password) < minpasswordlen:
      raise ValueError("must supply a valid password of at least %d characters" % minpasswordlen)
    userexists = session.loginchecker.userexists(username)
    if userexists:
      usernode = getattr(session.loginchecker.users, username)
      # use the email address on file
      email = getattr(usernode, "email", email)
      password = getattr(usernode, "passwdhash", "")
      # TODO: we can't figure out the password as we only store the md5sum. have a password reset mechanism
      message = "you (or someone else) requested your password... here is the md5sum of it, happy cracking\n"
      displaymessage = "that username already exists. emailing the password to the username's email address...\n"
      redirecturl = "login.html"
    else:
      setattr(session.loginchecker.users, username + ".email", email)
      setattr(session.loginchecker.users, username + ".passwdhash", session.md5hexdigest(password))
      message = "an account has been created for you\n"
      setattr(session.loginchecker.users, username + ".activated", 0)
      activationcode = self.generateactivationcode()
      setattr(session.loginchecker.users, username + ".activationcode", activationcode)
      message = "to activate it, enter the following activation code:\n%s\n" % activationcode
      displaymessage = "account created. will be emailed login details. enter activation code on the next page"
      redirecturl = "activate.html"
    self.saveuserprefs(session.loginchecker.users)
    message += "username: %s\npassword: %s\n" % (username, password)
    smtpserver = self.instance.registration.smtpserver
    fromaddress = self.instance.registration.fromaddress
    message = mailer.makemessage({"from": fromaddress, "to": [email], "subject": "Pootle Registration", "body": message})
    errmsg = mailer.dosendmessage(fromemail=self.instance.registration.fromaddress, recipientemails=[email], message=message, smtpserver=smtpserver)
    if errmsg:
      raise ValueError(errmsg)
    return displaymessage, redirecturl

  def registerpage(self, session, argdict):
    """handle registration or return the Register page"""
    if "username" in argdict:
      try:
        displaymessage, redirecturl = self.handleregistration(session, argdict)
      except ValueError, message:
        session.status = str(message)
        return RegisterPage(session, argdict)
      message = pagelayout.IntroText(displaymessage)
      redirectpage = pagelayout.PootlePage("Redirecting...", [message], session)
      redirectpage.attribs["refresh"] = 10
      redirectpage.attribs["refreshurl"] = redirecturl
      return redirectpage
    else:
      return RegisterPage(session, argdict)

  def activatepage(self, session, argdict):
    """handle activation or return the Register page"""
    if "username" in argdict and "activationcode" in argdict:
      username = argdict["username"]
      activationcode = argdict["activationcode"]
      usernode = getattr(session.loginchecker.users, username, None)
      if usernode is not None:
        correctcode = getattr(usernode, "activationcode", "")
        if correctcode and correctcode.strip().lower() == activationcode.strip().lower():
          setattr(usernode, "activated", 1)
          self.saveuserprefs(session.loginchecker.users)
          redirecttext = pagelayout.IntroText("Your account has been activated! Redirecting to login...")
          redirectpage = pagelayout.PootlePage("Redirecting to login...", redirecttext, session)
          redirectpage.attribs["refresh"] = 10
          redirectpage.attribs["refreshurl"] = "login.html"
          return redirectpage
      failedtext = pagelayout.IntroText("The activation link you have entered was not valid")
      failedpage = pagelayout.PootlePage("Activation Failed", failedtext, session)
      return failedpage
    else:
      return ActivatePage(session, argdict)

def main_is_frozen():
  import imp
  return (hasattr(sys, "frozen") or # new py2exe
          hasattr(sys, "importers") # old py2exe
          or imp.is_frozen("__main__")) # tools/freeze

if __name__ == '__main__':
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


