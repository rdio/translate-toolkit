#!/usr/bin/env python

from jToolkit.web import server
from jToolkit.web import session
from jToolkit.widgets import widgets
from jToolkit.widgets import form
from translate.pootle import pagelayout

class RegistrationError(ValueError):
  pass

class LoginPage(server.LoginPage, pagelayout.PootlePage):
  """wraps the normal login page in a PootlePage layout"""
  def __init__(self, session, extraargs={}, confirmlogin=0, specialmessage=None, languagenames=None):
    server.LoginPage.__init__(self, session, extraargs, confirmlogin, specialmessage, languagenames)
    contents = pagelayout.IntroText(self.contents)
    pagelayout.PootlePage.__init__(self, session.localize("Login to Pootle"), contents, session)

  def getcontents(self):
    return pagelayout.PootlePage.getcontents(self)

class RegisterPage(pagelayout.PootlePage):
  """page for new registrations"""
  def __init__(self, session, argdict):
    self.localize = session.localize
    introtext = [pagelayout.IntroText(self.localize("Please enter your registration details"))]
    if session.status:
      statustext = pagelayout.IntroText(session.status)
      introtext.append(statustext)
    self.argdict = argdict
    contents = [introtext, self.getform()]
    pagelayout.PootlePage.__init__(self, self.localize("Pootle Registration"), contents, session)

  def getform(self):
    columnlist = [("email", self.localize("Email Address"), self.localize("Must be a valid email address")),
                  ("username", self.localize("Username"), self.localize("Your requested username")),
                  ("password", self.localize("Password"), self.localize("Your desired password"))]
    formlayout = {1:("email", ), 2:("username", ), 3:("password", )}
    extrawidgets = [widgets.Input({'type': 'submit', 'name':'register', 'value':self.localize('Register')})]
    record = dict([(column[0], self.argdict.get(column[0], "")) for column in columnlist])
    return form.SimpleForm(record, "register", columnlist, formlayout, {}, extrawidgets)

class ActivatePage(pagelayout.PootlePage):
  """page for new registrations"""
  def __init__(self, session, argdict):
    self.localize = session.localize
    introtext = [pagelayout.IntroText(self.localize("Please enter your activation details"))]
    if session.status:
      statustext = pagelayout.IntroText(session.status)
      introtext.append(statustext)
    self.argdict = argdict
    contents = [introtext, self.getform()]
    pagelayout.PootlePage.__init__(self, self.localize("Pootle Account Activation"), contents, session)

  def getform(self):
    columnlist = [("username", self.localize("Username"), self.localize("Your requested username")),
                  ("activationcode", self.localize("Activation Code"), self.localize("The activation code you received"))]
    formlayout = {1:("username", ), 2:("activationcode", )}
    extrawidgets = [widgets.Input({'type': 'submit', 'name':'activate', 'value':self.localize('Activate Account')})]
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

