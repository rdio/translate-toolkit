#!/usr/bin/env python

from jToolkit.widgets import widgets
from jToolkit.widgets import table
from translate.pootle import pagelayout
from translate.pootle import projects
import os

def summarizestats(statslist, totalstats=None):
  if totalstats is None:
    totalstats = {}
  for statsdict in statslist:
    for name, count in statsdict.iteritems():
      totalstats[name] = totalstats.get(name, 0) + count
  return totalstats

class AboutPage(pagelayout.PootlePage):
  """the bar at the side describing current login details etc"""
  def __init__(self, session):
    self.localize = session.localize
    pagetitle = getattr(session.instance, "title")
    title = pagelayout.Title(pagetitle)
    description = pagelayout.IntroText(getattr(session.instance, "description"))
    abouttitle = pagelayout.Title(self.localize("About Pootle"))
    introtext = pagelayout.IntroText(self.localize("<strong>Pootle</strong> is a simple web portal that should allow you to <strong>translate</strong>! Since Pootle is <strong>Free Software</strong>, you can download it and run your own copy if you like. You can also help participate in the development in many ways (you don't have to be able to program)."))
    hosttext = pagelayout.IntroText(self.localize('The Pootle project itself is hosted at <a href="http://translate.sourceforge.net/">translate.sourceforge.net</a> where you can find the details about source code, mailing lists etc.'))
    nametext = pagelayout.IntroText(self.localize('The name stands for <b>PO</b>-based <b>O</b>nline <b>T</b>ranslation / <b>L</b>ocalization <b>E</b>ngine, but you may need to read <a href="http://www.thechestnut.com/flumps.htm">this</a>.'))
    aboutpootle = [abouttitle, introtext, hosttext, nametext]
    contents = pagelayout.Contents([title, description, aboutpootle])
    pagelayout.PootlePage.__init__(self, pagetitle, contents, session)

class PootleIndex(pagelayout.PootlePage):
  """the main page"""
  def __init__(self, potree, session):
    self.potree = potree
    self.localize = session.localize
    aboutlink = pagelayout.IntroText(widgets.Link("about.html", self.localize("About this Pootle server")))
    languagelinks = self.getlanguagelinks()
    projectlinks = self.getprojectlinks()
    contents = [aboutlink, languagelinks, projectlinks]
    pagelayout.PootlePage.__init__(self, self.localize("Pootle"), contents, session)

  def getlanguagelinks(self):
    """gets the links to the languages"""
    languagestitle = pagelayout.Title(self.localize('Languages'))
    languagelinks = []
    for languagecode in self.potree.getlanguagecodes():
      languagename = self.potree.getlanguagename(languagecode)
      languagelink = widgets.Link(languagecode+"/", languagename)
      languagelinks.append(languagelink)
    listwidget = widgets.SeparatedList(languagelinks, ", ")
    bodydescription = pagelayout.ItemDescription(listwidget)
    return pagelayout.Contents([languagestitle, bodydescription])

  def getprojectlinks(self):
    """gets the links to the projects"""
    projectstitle = pagelayout.Title(widgets.Link("projects/", self.localize("Projects")))
    projectlinks = []
    for projectcode in self.potree.getprojectcodes():
      projectname = self.potree.getprojectname(projectcode)
      projectdescription = self.potree.getprojectdescription(projectcode)
      projectlink = widgets.Link("projects/%s/" % projectcode, projectname, {"title":projectdescription})
      projectlinks.append(projectlink)
    listwidget = widgets.SeparatedList(projectlinks, ", ")
    bodydescription = pagelayout.ItemDescription(listwidget)
    return pagelayout.Contents([projectstitle, bodydescription])

class UserIndex(pagelayout.PootlePage):
  """home page for a given user"""
  def __init__(self, potree, session):
    self.potree = potree
    self.session = session
    self.localize = session.localize
    optionslink = pagelayout.IntroText(widgets.Link("options.html", self.localize("Change options")))
    contents = [self.getquicklinks(), optionslink]
    if session.issiteadmin():
      adminlink = pagelayout.IntroText(widgets.Link("../admin/", self.localize("Admin page")))
      contents.append(adminlink)
    pagelayout.PootlePage.__init__(self, self.localize("User Page for: %s") % session.username, contents, session)

  def getquicklinks(self):
    """gets a set of quick links to user's project-languages"""
    quicklinkstitle = pagelayout.Title(self.localize("Quick Links"))
    quicklinks = []
    for languagecode in self.session.getlanguages():
      languagename = self.potree.getlanguagename(languagecode)
      languagelink = widgets.Link("../%s/" % languagecode, languagename)
      quicklinks.append(pagelayout.Title(languagelink))
      languagelinks = []
      for projectcode in self.session.getprojects():
        if self.potree.hasproject(languagecode, projectcode):
          projectname = self.potree.getprojectname(projectcode)
          projecturl = "../%s/%s/" % (languagecode, projectcode)
          projecttitle = self.localize("%s %s") % (languagename, projectname)
          languagelinks.append([widgets.Link(projecturl, projecttitle), "<br/>"])
      quicklinks.append(pagelayout.ItemDescription(languagelinks))
    if not quicklinks:
      setoptionstext = self.localize("Please click on 'Change options' and select some languages and projects")
      quicklinks.append(pagelayout.ItemDescription(setoptionstext))
    return pagelayout.Contents([quicklinkstitle, quicklinks])

class UserOptions(pagelayout.PootlePage):
  """page for user to change their options"""
  def __init__(self, potree, session):
    self.potree = potree
    self.session = session
    self.localize = session.localize
    submitbutton = widgets.Input({"type":"submit", "name":"changeoptions", "value": self.localize("Save changes")})
    hiddenfields = widgets.HiddenFieldList([("allowmultikey","languages"), ("allowmultikey","projects")])
    formmembers = [self.getprojectoptions(), self.getlanguageoptions(), hiddenfields, submitbutton]
    useroptions = widgets.Form(formmembers, {"name": "useroptions", "action":""})
    homelink = pagelayout.IntroText(widgets.Link("index.html", self.localize("Home page")))
    contents = [self.getpersonaloptions(), useroptions, homelink]
    pagelayout.PootlePage.__init__(self, self.localize("Options for: %s") % session.username, contents, session)

  def getprojectoptions(self):
    """gets the options box to change the user's projects"""
    projectstitle = pagelayout.Title(self.localize("My Projects"))
    projectoptions = []
    userprojects = self.session.getprojects()
    for projectcode in self.potree.getprojectcodes():
      projectname = self.potree.getprojectname(projectcode)
      projectoptions.append((projectcode, projectname))
    projectselect = widgets.MultiSelect({"value": userprojects, "name": "projects"}, projectoptions)
    bodydescription = pagelayout.ItemDescription([projectselect, widgets.HiddenFieldList({"allowmultikey":"projects"})])
    return pagelayout.Contents([projectstitle, bodydescription])

  def getlanguageoptions(self):
    """gets the options box to change the user's languages"""
    languagestitle = pagelayout.Title(self.localize("My Languages"))
    languageoptions = []
    userlanguages = self.session.getlanguages()
    for languagecode in self.potree.getlanguagecodes():
      languagename = self.potree.getlanguagename(languagecode)
      languageoptions.append((languagecode, languagename))
    languageselect = widgets.MultiSelect({"value": userlanguages, "name": "languages"}, languageoptions)
    bodydescription = pagelayout.ItemDescription(languageselect)
    return pagelayout.Contents([languagestitle, bodydescription])

  def getpersonaloptions(self):
    """get the options fields to change the user's personal details"""
    personaltitle = pagelayout.Title(self.localize("Personal Details"))
    personal = table.TableLayout()
    personal.setcell(0, 0, table.TableCell(pagelayout.Title(self.localize("Option"))))
    personal.setcell(0, 1, table.TableCell(pagelayout.Title(self.localize("Current value"))))
    for optionname in ("name", "email"):
      optionvalue = getattr(self.session.prefs, optionname, "")
      valuetextbox = widgets.Input({"name": "option-%s" % optionname, "value": optionvalue})
      rownum = personal.maxrownum()+1
      personal.setcell(rownum, 0, table.TableCell(optionname))
      personal.setcell(rownum, 1, table.TableCell(valuetextbox))
    rownum = personal.maxrownum()+1
    submitbutton = widgets.Input({"type":"submit", "name":"changepersonal", "value":self.localize("Save changes")})
    personalform = widgets.Form([personal, submitbutton], {"name": "personal", "action":""})
    return pagelayout.Contents([personaltitle, personalform])

class AdminPage(pagelayout.PootlePage):
  """page for administering pootle..."""
  def __init__(self, potree, session, instance):
    self.potree = potree
    self.session = session
    self.instance = instance
    self.localize = session.localize
    if self.session.issiteadmin():
      homelink = pagelayout.IntroText(widgets.Link("../home/", self.localize("Home page")))
      userslink = pagelayout.IntroText(widgets.Link("users.html", self.localize("Users")))
      langlink = pagelayout.IntroText(widgets.Link("languages.html", self.localize("Languages")))
      projlink = pagelayout.IntroText(widgets.Link("projects.html", self.localize("Projects")))
      contents = [homelink, userslink, langlink, projlink, self.getgeneral()]
    else:
      contents = pagelayout.IntroText(self.localize("You do not have the rights to administer pootle."))
    pagelayout.PootlePage.__init__(self, self.localize("Pootle Admin Page"), contents, session)

  def getgeneral(self):
    """gets the general options"""
    generaltitle = pagelayout.Title(self.localize('General Options'))
    general = table.TableLayout()
    general.setcell(0, 0, table.TableCell(pagelayout.Title(self.localize("Option"))))
    general.setcell(0, 1, table.TableCell(pagelayout.Title(self.localize("Current value"))))
    for optionname in ("title", "description", "baseurl"):
      optionvalue = getattr(self.instance, optionname, "")
      valuetextbox = widgets.Input({"name": "option-%s" % optionname, "value": optionvalue})
      rownum = general.maxrownum()+1
      general.setcell(rownum, 0, table.TableCell(optionname))
      general.setcell(rownum, 1, table.TableCell(valuetextbox))
    rownum = general.maxrownum()+1
    submitbutton = widgets.Input({"type":"submit", "name":"changegeneral", "value":self.localize("Save changes")})
    generalform = widgets.Form([general, submitbutton], {"name": "general", "action":""})
    return pagelayout.Contents([generaltitle, generalform])

class LanguagesAdminPage(pagelayout.PootlePage):
  """page for administering pootle..."""
  def __init__(self, potree, session, instance):
    self.potree = potree
    self.session = session
    self.instance = instance
    self.localize = session.localize
    if self.session.issiteadmin():
      homelink = pagelayout.IntroText(widgets.Link("../home/", self.localize("Home page")))
      indexlink = pagelayout.IntroText(widgets.Link("index.html", self.localize("Main Admin page")))
      contents = [homelink, indexlink, self.getlanguages()]
    else:
      contents = pagelayout.IntroText(self.localize("You do not have the rights to administer pootle."))
    pagelayout.PootlePage.__init__(self, self.localize("Pootle Languages Admin Page"), contents, session)

  def getlanguages(self):
    """gets the links to the languages"""
    languagestitle = pagelayout.Title(self.localize('Languages'))
    languages = table.TableLayout()
    languages.setcell(0, 0, table.TableCell(pagelayout.Title(self.localize("ISO Code"))))
    languages.setcell(0, 1, table.TableCell(pagelayout.Title(self.localize("Full Name"))))
    languages.setcell(0, 2, table.TableCell(pagelayout.Title(self.localize("Remove language"))))
    for languagecode in self.potree.getlanguagecodes():
      languagename = self.potree.getlanguagename(languagecode)
      nametextbox = widgets.Input({"name": "languagename-%s" % languagecode, "value": languagename})
      removecheckbox = widgets.Input({"name": "languageremove-%s" % languagecode, "type": "checkbox"})
      rownum = languages.maxrownum()+1
      languages.setcell(rownum, 0, table.TableCell(languagecode))
      languages.setcell(rownum, 1, table.TableCell(nametextbox))
      languages.setcell(rownum, 2, table.TableCell([removecheckbox, self.localize("Remove %s") % languagecode]))
    rownum = languages.maxrownum()+1
    codetextbox = widgets.Input({"name": "newlanguagecode", "value": "", "size": 6})
    nametextbox = widgets.Input({"name": "newlanguagename", "value": self.localize("(add language here)")})
    languages.setcell(rownum, 0, table.TableCell(codetextbox))
    languages.setcell(rownum, 1, table.TableCell(nametextbox))
    submitbutton = widgets.Input({"type":"submit", "name":"changelanguages", "value":self.localize("Save changes")})
    languageform = widgets.Form([languages, submitbutton], {"name": "languages", "action":""})
    return pagelayout.Contents([languagestitle, languageform])

class ProjectsAdminPage(pagelayout.PootlePage):
  """page for administering pootle..."""
  def __init__(self, potree, session, instance):
    self.potree = potree
    self.session = session
    self.instance = instance
    self.localize = session.localize
    if self.session.issiteadmin():
      homelink = pagelayout.IntroText(widgets.Link("../home/", self.localize("Home page")))
      indexlink = pagelayout.IntroText(widgets.Link("index.html", self.localize("Main Admin page")))
      contents = [homelink, indexlink, self.getprojects()]
    else:
      contents = pagelayout.IntroText(self.localize("You do not have the rights to administer pootle."))
    pagelayout.PootlePage.__init__(self, self.localize("Pootle Projects Admin Page"), contents, session)

  def getprojects(self):
    """gets the links to the projects"""
    projectstitle = pagelayout.Title(self.localize("Projects"))
    projects = table.TableLayout()
    projects.setcell(0, 0, table.TableCell(pagelayout.Title(self.localize("Project Code"))))
    projects.setcell(0, 1, table.TableCell(pagelayout.Title(self.localize("Full Name"))))
    projects.setcell(0, 2, table.TableCell(pagelayout.Title(self.localize("Project Description"))))
    projects.setcell(0, 3, table.TableCell(pagelayout.Title(self.localize("Checker Style"))))
    projects.setcell(0, 4, table.TableCell(pagelayout.Title(self.localize("Create MO Files"))))
    projects.setcell(0, 5, table.TableCell(pagelayout.Title(self.localize("Remove project"))))
    for projectcode in self.potree.getprojectcodes():
      projectadminlink = "../projects/%s/admin.html" % projectcode
      projectname = self.potree.getprojectname(projectcode)
      projectdescription = self.potree.getprojectdescription(projectcode)
      projectname = self.potree.getprojectname(projectcode)
      projectcheckerstyle = self.potree.getprojectcheckerstyle(projectcode)
      if self.potree.getprojectcreatemofiles(projectcode):
        projectcreatemofiles = "checked"
      else:
        projectcreatemofiles = ""
      nametextbox = widgets.Input({"name": "projectname-%s" % projectcode, "value": projectname})
      descriptiontextbox = widgets.Input({"name": "projectdescription-%s" % projectcode, "value": projectdescription})
      checkerstyletextbox = widgets.Input({"name": "projectcheckerstyle-%s" % projectcode, "value": projectcheckerstyle})
      createmofilescheckbox = widgets.Input({"name": "projectcreatemofiles-%s" % projectcode, "value": projectcreatemofiles, "type": "checkbox", projectcreatemofiles:''})
      removecheckbox = widgets.Input({"name": "projectremove-%s" % projectcode, "type": "checkbox"})
      rownum = projects.maxrownum()+1
      projects.setcell(rownum, 0, table.TableCell(widgets.Link(projectadminlink, projectcode)))
      projects.setcell(rownum, 1, table.TableCell(nametextbox))
      projects.setcell(rownum, 2, table.TableCell(descriptiontextbox))
      projects.setcell(rownum, 3, table.TableCell(checkerstyletextbox))
      projects.setcell(rownum, 4, table.TableCell(createmofilescheckbox))
      projects.setcell(rownum, 5, table.TableCell([removecheckbox, self.localize("Remove %s") % projectcode]))
    rownum = projects.maxrownum()+1
    codetextbox = widgets.Input({"name": "newprojectcode", "value": "", "size": 6})
    nametextbox = widgets.Input({"name": "newprojectname", "value": self.localize("(add project here)")})
    descriptiontextbox = widgets.Input({"name": "newprojectdescription", "value": self.localize("(project description)")})
    checkerstyletextbox = widgets.Input({"name": "newprojectcheckerstyle", "value": self.localize("(checker style)")})
    createmofilescheckbox = widgets.Input({"name": "newprojectcreatemofiles", "type": "checkbox"})
    projects.setcell(rownum, 0, table.TableCell(codetextbox))
    projects.setcell(rownum, 1, table.TableCell(nametextbox))
    projects.setcell(rownum, 2, table.TableCell(descriptiontextbox))
    projects.setcell(rownum, 3, table.TableCell(checkerstyletextbox))
    projects.setcell(rownum, 4, table.TableCell(createmofilescheckbox))
    submitbutton = widgets.Input({"type":"submit", "name":"changeprojects", "value":self.localize("Save changes")})
    projectform = widgets.Form([projects, submitbutton], {"name": "projects", "action":""})
    return pagelayout.Contents([projectstitle, projectform])

class UsersAdminPage(pagelayout.PootlePage):
  """page for administering pootle..."""
  def __init__(self, server, users, session, instance):
    self.server = server
    self.users = users
    self.session = session
    self.instance = instance
    self.localize = session.localize
    if self.session.issiteadmin():
      homelink = pagelayout.IntroText(widgets.Link("../home/", self.localize("Home page")))
      adminlink = pagelayout.IntroText(widgets.Link("index.html", self.localize("Admin page")))
      contents = [homelink, adminlink, self.getusers()]
    else:
      contents = pagelayout.IntroText(self.localize("You do not have the rights to administer Pootle."))
    pagelayout.PootlePage.__init__(self, self.localize("Pootle User Admin Page"), contents, session)

  def getusers(self):
    """user list and adding"""
    userstitle = pagelayout.Title(self.localize("Users"))
    users = table.TableLayout()
    users.setcell(0, 0, table.TableCell(pagelayout.Title(self.localize("Login"))))
    users.setcell(0, 1, table.TableCell(pagelayout.Title(self.localize("Full Name"))))
    users.setcell(0, 2, table.TableCell(pagelayout.Title(self.localize("Email Address"))))
    users.setcell(0, 3, table.TableCell(pagelayout.Title(self.localize("Password"))))
    # users.setcell(0, 2, table.TableCell(pagelayout.Title(self.localize("Activated"))))
    # users.setcell(0, 3, table.TableCell(pagelayout.Title(self.localize("Projects"))))
    # users.setcell(0, 4, table.TableCell(pagelayout.Title(self.localize("Languages"))))
    for username, usernode in self.users.iteritems():
      fullnametextbox = widgets.Input({"name": "userfullname-%s" % username, "value": getattr(usernode, "name", "")})
      emailtextbox = widgets.Input({"name": "useremail-%s" % username, "value": usernode.email})
      removecheckbox = widgets.Input({"name": "userremove-%s" % username, "type": "checkbox"})
      rownum = users.maxrownum()+1
      users.setcell(rownum, 0, table.TableCell(username))
      users.setcell(rownum, 1, table.TableCell(fullnametextbox))
      users.setcell(rownum, 2, table.TableCell(emailtextbox))
      # users.setcell(rownum, 2, table.TableCell(descriptiontextbox))
      # users.setcell(rownum, 3, table.TableCell(checkerstyletextbox))
      users.setcell(rownum, 4, table.TableCell([removecheckbox, self.localize("Remove %s") % username]))
    rownum = users.maxrownum()+1
    codetextbox = widgets.Input({"name": "newusername", "value": "", "size": 6})
    newfullnametextbox = widgets.Input({"name": "newfullname", "value": self.localize("(add full name here)")})
    newemailtextbox = widgets.Input({"name": "newuseremail", "value": self.localize("(add email here)")})
    passwordtextbox = widgets.Input({"name": "newuserpassword", "value": self.localize("(add password here)")})
    # sendemailcheckbox = widgets.Input({"name": "newusersendemail", "type": "checkbox", "checked": "true"})
    activatecheckbox = widgets.Input({"name": "newuseractivate", "type": "checkbox", "checked": "true"})
    users.setcell(rownum, 0, table.TableCell(codetextbox))
    users.setcell(rownum, 1, table.TableCell(newfullnametextbox))
    users.setcell(rownum, 2, table.TableCell(newemailtextbox))
    users.setcell(rownum, 3, table.TableCell(passwordtextbox))
    # users.setcell(rownum, 3, table.TableCell([sendemailcheckbox, self.localize("Email New User")]))
    users.setcell(rownum, 4, table.TableCell([activatecheckbox, self.localize("Activate New User")]))
    submitbutton = widgets.Input({"type":"submit", "name":"changeusers", "value":self.localize("Save changes")})
    userform = widgets.Form([users, submitbutton], {"name": "users", "action":""})
    return pagelayout.Contents([userstitle, userform])

class ProjectsIndex(PootleIndex):
  """the list of projects"""
  def getlanguagelinks(self):
    """we don't need language links on the project page"""
    return ""

  def getprojectlinks(self):
    """gets the links to the projects"""
    projectstitle = pagelayout.Title(self.localize("Projects"))
    projectlinks = []
    for projectcode in self.potree.getprojectcodes():
      projectname = self.potree.getprojectname(projectcode)
      projectdescription = self.potree.getprojectdescription(projectcode)
      projectlink = widgets.Link("%s/" % projectcode, projectname, {"title":projectdescription})
      projectlinks.append(projectlink)
    listwidget = widgets.SeparatedList(projectlinks, ", ")
    bodydescription = pagelayout.ItemDescription(listwidget)
    return pagelayout.Contents([projectstitle, bodydescription])

class LanguageIndex(pagelayout.PootlePage):
  """the main page"""
  def __init__(self, potree, languagecode, session):
    self.potree = potree
    self.languagecode = languagecode
    self.localize = session.localize
    languagename = self.potree.getlanguagename(self.languagecode)
    projectlinks = self.getprojectlinks()
    pagelayout.PootlePage.__init__(self, "Pootle: "+languagename, projectlinks, session, bannerheight=81)

  def getprojectlinks(self):
    """gets the links to the projects"""
    projectcodes = self.potree.getprojectcodes(self.languagecode)
    projectitems = [self.getprojectitem(projectcode) for projectcode in projectcodes]
    return pagelayout.Contents(projectitems)

  def getprojectitem(self, projectcode):
    projectname = self.potree.getprojectname(projectcode)
    bodytitle = pagelayout.Title(projectname)
    projectdescription = self.potree.getprojectdescription(projectcode)
    bodydescription = pagelayout.ItemDescription(widgets.Link(projectcode+"/", self.localize('%s project') % projectname, {"title":projectdescription}))
    body = pagelayout.ContentsItem([bodytitle, bodydescription])
    project = self.potree.getproject(self.languagecode, projectcode)
    numfiles = len(project.pofilenames)
    projectstats = project.calculatestats()
    translated = projectstats.get("translated", 0)
    total = projectstats.get("total", 0)
    percentfinished = (translated*100/max(total, 1))
    stats = pagelayout.ItemStatistics(self.localize("%d files, %d/%d strings (%d%%) translated") % (numfiles, translated, total, percentfinished))
    return pagelayout.Item([body, stats])

class ProjectLanguageIndex(pagelayout.PootlePage):
  """list of languages belonging to a project"""
  def __init__(self, potree, projectcode, session):
    self.potree = potree
    self.projectcode = projectcode
    self.localize = session.localize
    projectname = self.potree.getprojectname(self.projectcode)
    languagelinks = self.getlanguagelinks()
    pagelayout.PootlePage.__init__(self, "Pootle: "+projectname, languagelinks, session, bannerheight=81)

  def getlanguagelinks(self):
    """gets the links to the languages"""
    languagecodes = self.potree.getlanguagecodes(self.projectcode)
    languageitems = [self.getlanguageitem(languagecode) for languagecode in languagecodes]
    return pagelayout.Contents(languageitems)

  def getlanguageitem(self, languagecode):
    languagename = self.potree.getlanguagename(languagecode)
    bodytitle = pagelayout.Title(languagename)
    bodydescription = pagelayout.ItemDescription(widgets.Link("../../%s/%s/" % (languagecode, self.projectcode), self.localize('%s language') % languagename))
    body = pagelayout.ContentsItem([bodytitle, bodydescription])
    language = self.potree.getproject(languagecode, self.projectcode)
    numfiles = len(language.pofilenames)
    languagestats = language.calculatestats()
    translated = languagestats.get("translated", 0)
    total = languagestats.get("total", 0)
    percentfinished = (translated*100/max(total, 1))
    stats = pagelayout.ItemStatistics(self.localize("%d files, %d/%d strings (%d%%) translated") % (numfiles, translated, total, percentfinished))
    return pagelayout.Item([body, stats])

class ProjectAdminPage(pagelayout.PootlePage):
  """list of languages belonging to a project"""
  def __init__(self, potree, projectcode, session, argdict):
    self.potree = potree
    self.projectcode = projectcode
    self.session = session
    self.localize = session.localize
    projectname = self.potree.getprojectname(self.projectcode)
    if self.session.issiteadmin():
      if "doaddlanguage" in argdict:
        newlanguage = argdict.get("newlanguage", None)
        if not newlanguage:
          raise ValueError("You must select a new language")
        self.potree.addtranslationproject(newlanguage, self.projectcode)
      if "doupdatelanguage" in argdict:
        languagecode = argdict.get("updatelanguage", None)
        if not languagecode:
          raise ValueError("No languagecode given in doupdatelanguage")
        translationproject = self.potree.getproject(languagecode, self.projectcode)
        translationproject.converttemplates()
      languagestitle = pagelayout.Title(self.localize("Existing languages"))
      languagelinks = self.getlanguagelinks()
      existing = pagelayout.ContentsItem([languagestitle, languagelinks])
      newlangform = self.getnewlangform()
      contents = [existing, newlangform]
    else:
      contents = pagelayout.IntroText(self.localize("You do not have the rights to administer this project."))
    pagelayout.PootlePage.__init__(self, "Pootle Admin: "+projectname, contents, session, bannerheight=81)

  def getlanguagelinks(self):
    """gets the links to the languages"""
    languagecodes = self.potree.getlanguagecodes(self.projectcode)
    languageitems = [self.getlanguageitem(languagecode) for languagecode in languagecodes]
    return pagelayout.Item(languageitems)

  def getlanguageitem(self, languagecode):
    languagename = self.potree.getlanguagename(languagecode)
    adminlink = widgets.Link("../../%s/%s/" % (languagecode, self.projectcode), languagename)
    updatelink = widgets.Link("?doupdatelanguage=1&updatelanguage=%s" % languagecode, self.localize("Update from templates"))
    return pagelayout.ItemDescription([adminlink, updatelink])

  def getnewlangform(self):
    """returns a box that lets the user add new languages"""
    existingcodes = self.potree.getlanguagecodes(self.projectcode)
    allcodes = self.potree.getlanguagecodes()
    newcodes = [code for code in allcodes if not code in existingcodes]
    newcodes.sort()
    newoptions = [(code, self.potree.getlanguagename(code)) for code in newcodes]
    languageselect = widgets.Select({'name':'newlanguage'}, options=newoptions)
    submitbutton = widgets.Input({"type": "submit", "name": "doaddlanguage", "value": self.localize("Add Language")})
    newlangform = widgets.Form([languageselect, submitbutton], {"action": "", "name":"newlangform"})
    return newlangform

class ProjectIndex(pagelayout.PootlePage):
  """the main page"""
  def __init__(self, project, session, argdict, dirfilter=None):
    self.project = project
    self.session = self.project.gettranslationsession(session)
    self.localize = session.localize
    self.rights = self.session.getrights()
    message = argdict.get("message", "")
    if message:
      message = pagelayout.IntroText(message)
    if dirfilter == "":
      dirfilter = None
    self.dirfilter = dirfilter
    if dirfilter and dirfilter.endswith(".po"):
      self.dirname = "/".join(dirfilter.split("/")[:-1])
    else:
      self.dirname = dirfilter or ""
    self.argdict = argdict
    # handle actions before generating URLs, so we strip unneccessary parameters out of argdict
    self.handleactions()
    self.showtracks = self.getboolarg("showtracks")
    self.showchecks = self.getboolarg("showchecks")
    self.showassigns = self.getboolarg("showassigns")
    currentfolder = dirfilter
    if currentfolder:
      depth = currentfolder.count("/") + 1
      rootlink = "/".join([".."] * depth) + "/index.html"
    else:
      rootlink = "index.html"
    language = widgets.Link("../" + rootlink, self.project.languagename)
    project = widgets.Link( self.getbrowseurl(rootlink), self.project.projectname)
    baselinks = ["[ ", language, "] [ ", project, "]"]
    pathlinks = []
    if dirfilter:
      dirs = self.dirfilter.split("/")
      count = len(dirs)
      for dir in dirs:
        backlinks = ""
        for i in range(count):
          backlinks = backlinks + "../"
        count = count - 1
        dirlink = widgets.Link(self.getbrowseurl(backlinks + dir + "/"), dir)
        pathlinks.append(dirlink)
        if count != 0:
          pathlinks.append("/ ")
    navbarpath = pagelayout.Title(baselinks + [" "] + pathlinks)
    if dirfilter and dirfilter.endswith(".po"):
      actionlinks = []
      mainstats = []
      mainicon = pagelayout.Icon("file.png")
    else:
      pofilenames = self.project.browsefiles(dirfilter)
      projectstats = self.project.calculatestats(pofilenames)
      actionlinks = self.getactionlinks("", projectstats, ["review", "check", "assign", "quick", "all"])
      actionlinks = pagelayout.ActionLinks(actionlinks)
      mainstats = self.getitemstats("", projectstats, len(pofilenames))
      mainicon = pagelayout.Icon("folder.png")
    mainitem = pagelayout.MainItem([mainicon, navbarpath, actionlinks, mainstats])
    childitems = self.getchilditems(dirfilter)
    pagetitle = self.localize("Pootle: Project %s, Language %s") % (self.project.projectname, self.project.languagename)
    pagelayout.PootlePage.__init__(self, pagetitle, [message, mainitem, childitems], session, bannerheight=81, returnurl="%s/%s/%s" % (self.project.languagecode, self.project.projectcode, self.dirname))
    self.addsearchbox(searchtext="", action="translate.html")
    if session.issiteadmin() and self.showassigns:
      self.addassignbox()
    if session.issiteadmin():
      self.adduploadbox()
    self.addnavlinks(dirfilter)

  def handleactions(self):
    """handles the given actions that must be taken (changing operations)"""
    if "doassign" in self.argdict:
      assignto = self.argdict.pop("assignto", None)
      action = self.argdict.pop("action", None)
      if not assignto and action:
        raise ValueError("cannot doassign, need assignto and action")
      search = projects.Search(dirfilter=self.dirfilter)
      assigncount = self.project.assignpoitems(search, assignto, action)
      print "assigned %d strings to %s for %s" % (assigncount, assignto, action)
      del self.argdict["doassign"]
    if self.getboolarg("removeassigns"):
      assignedto = self.argdict.pop("assignedto", None)
      removefilter = self.argdict.pop("removefilter", "")
      if removefilter:
        if self.dirfilter:
          removefilter = self.dirfilter + removefilter
      else:
        removefilter = self.dirfilter
      search = projects.Search(dirfilter=removefilter)
      search.assignedto = assignedto
      assigncount = self.project.unassignpoitems(search, assignedto)
      print "removed %d assigns from %s" % (assigncount, assignedto)
      del self.argdict["removeassigns"]
    if "doupload" in self.argdict:
      uploadfile = self.argdict.pop("uploadfile", None)
      if not uploadfile:
        raise ValueError("cannot upload file, no file attached")
      if uploadfile.filename.endswith(".po"):
        self.project.uploadpofile(self.dirname, uploadfile.filename, uploadfile.contents)
      elif uploadfile.filename.endswith(".zip"):
        self.project.uploadarchive(self.dirname, uploadfile.contents)
      else:
        raise ValueError("can only upload PO files and zips of PO files")
      del self.argdict["doupload"]

  def getboolarg(self, argname, default=False):
    """gets a boolean argument from self.argdict"""
    value = self.argdict.get(argname, default)
    if isinstance(value, bool):
      return value
    elif isinstance(value, int):
      return bool(value)
    elif isinstance(value, (str, unicode)):
      value = value.lower() 
      if value.isdigit():
        return bool(int(value))
      if value == "true":
        return True
      if value == "false":
        return False
    raise ValueError("Invalid boolean value for %s: %r" % (argname, value))

  def makelink(self, link, **newargs):
    """constructs a link that keeps sticky arguments e.g. showchecks"""
    combinedargs = self.argdict.copy()
    combinedargs.update(newargs)
    if '?' in link:
      if not (link.endswith("&") or link.endswith("?")):
        link += "&"
    else:
      link += '?'
    # TODO: check escaping
    link += "&".join(["%s=%s" % (arg, value) for arg, value in combinedargs.iteritems()])
    return link

  def addnavlinks(self, dirfilter):
    """add navigation links to the sidebar"""
    if dirfilter and dirfilter.endswith(".po"):
      currentfolder = "/".join(dirfilter.split("/")[:-1])
    else:
      currentfolder = dirfilter
    if "archive" in self.rights:
      if currentfolder:
        archivename = "%s-%s-%s.zip" % (self.project.projectcode, self.project.languagecode, currentfolder.replace("/", "-"))
      else:
        archivename = "%s-%s.zip" % (self.project.projectcode, self.project.languagecode)
      self.addfolderlinks(self.localize("zip of folder"), archivename, archivename, enhancelink=False)

  def addfolderlinks(self, title, foldername, folderlink, tooltip=None, enhancelink=True):
    """adds a folder link to the sidebar"""
    if enhancelink:
      folderlink = self.makelink(folderlink)
    return pagelayout.PootlePage.addfolderlinks(self, title, foldername, folderlink, tooltip)

  def addassignbox(self):
    """adds a box that lets the user assign strings"""
    self.links.addcontents(pagelayout.SidebarTitle(self.localize("Assign Strings")))
    assigntobox = widgets.Input({"name": "assignto", "value": "", "title": self.localize("Assign to User")})
    actionbox = widgets.Input({"name": "action", "value": "translate", "title": self.localize("Assign Action")})
    submitbutton = widgets.Input({"type": "submit", "name": "doassign", "value": self.localize("Assign Strings")})
    assignform = widgets.Form([assigntobox, actionbox, submitbutton], {"action": "", "name":"assignform"})
    self.links.addcontents(assignform)

  def adduploadbox(self):
    """adds a box that lets the user assign strings"""
    self.links.addcontents(pagelayout.SidebarTitle(self.localize("Upload File")))
    filebox = widgets.Input({"type": "file", "name": "uploadfile", "title": self.localize("Select file to upload")})
    submitbutton = widgets.Input({"type": "submit", "name": "doupload", "value": self.localize("Upload File")})
    uploadform = widgets.Form([filebox, submitbutton], {"action": "", "name":"uploadform", "enctype": "multipart/form-data"})
    self.links.addcontents(uploadform)

  def getchilditems(self, dirfilter):
    """get all the items for directories and files viewable at this level"""
    if dirfilter is None:
      depth = 0
    else:
      depth = dirfilter.count(os.path.sep)
      if not dirfilter.endswith(os.path.extsep + "po"):
        depth += 1
    diritems = []
    for childdir in self.project.browsefiles(dirfilter=dirfilter, depth=depth, includedirs=True, includefiles=False):
      diritem = self.getdiritem(childdir)
      diritems.append((childdir, diritem))
    diritems.sort()
    fileitems = []
    for childfile in self.project.browsefiles(dirfilter=dirfilter, depth=depth, includefiles=True, includedirs=False):
      fileitem = self.getfileitem(childfile)
      fileitems.append((childfile, fileitem))
    fileitems.sort()
    childitems = [diritem for childdir, diritem in diritems] + [fileitem for childfile, fileitem in fileitems]
    polarity = False
    for childitem in childitems:
      childitem.setpolarity(polarity)
      polarity = not polarity
    return childitems

  def getdiritem(self, direntry):
    """returns an item showing a directory entry"""
    pofilenames = self.project.browsefiles(direntry)
    projectstats = self.project.calculatestats(pofilenames)
    basename = os.path.basename(direntry)
    bodytitle = pagelayout.Title(basename)
    basename += "/"
    folderimage = pagelayout.Icon("folder.png")
    browseurl = self.getbrowseurl(basename)
    bodytitle = widgets.Link(browseurl, bodytitle)
    actionlinks = self.getactionlinks(basename, projectstats)
    bodydescription = pagelayout.ActionLinks(actionlinks)
    body = pagelayout.ContentsItem([folderimage, bodytitle, bodydescription])
    stats = self.getitemstats(basename, projectstats, len(pofilenames))
    return pagelayout.Item([body, stats])

  def getfileitem(self, fileentry):
    """returns an item showing a file entry"""
    basename = os.path.basename(fileentry)
    projectstats = self.project.calculatestats([fileentry])
    folderimage = pagelayout.Icon("file.png")
    browseurl = self.getbrowseurl(basename)
    bodytitle = pagelayout.Title(widgets.Link(browseurl, basename))
    actionlinks = self.getactionlinks(basename, projectstats)
    downloadlink = widgets.Link(basename, self.localize('PO file'))
    csvname = basename.replace(".po", ".csv")
    csvlink = widgets.Link(csvname, self.localize('CSV file'))
    if self.project.hascreatemofiles(self.project.projectcode) and "pocompile" in self.rights:
      moname = basename.replace(".po", ".mo")
      molink = widgets.Link(moname, self.localize('MO file'))
      bodydescription = pagelayout.ActionLinks(actionlinks + [downloadlink, csvlink, molink])
    else:
      bodydescription = pagelayout.ActionLinks(actionlinks + [downloadlink, csvlink])
    body = pagelayout.ContentsItem([folderimage, bodytitle, bodydescription])
    stats = self.getitemstats(basename, projectstats, None)
    return pagelayout.Item([body, stats])

  def getbrowseurl(self, basename):
    """gets the link to browse the item"""
    if not basename or basename.endswith("/"):
      return self.makelink(basename or "index.html")
    else:
      return self.makelink(basename, translate=1, view=1)

  def getactionlinks(self, basename, projectstats, linksrequired=None):
    """get links to the actions that can be taken on an item (directory / file)"""
    if linksrequired is None:
      linksrequired = ["review", "quick", "all"]
    actionlinks = []
    if not basename or basename.endswith("/"):
      baseactionlink = basename + "translate.html?"
      baseindexlink = basename + "index.html?"
    else:
      baseactionlink = "%s?translate=1" % basename
      baseindexlink = "%s?index=1" % basename
    if "track" in linksrequired:
      if self.showtracks:
        trackslink = widgets.Link(self.makelink(baseindexlink, showtracks=0), self.localize("Hide Tracks"))
      else:
        trackslink = widgets.Link(self.makelink(baseindexlink, showtracks=1), self.localize("Show Tracks"))
      actionlinks.append(trackslink)
    if "check" in linksrequired and "translate" in self.rights:
      if self.showchecks:
        checkslink = widgets.Link(self.makelink(baseindexlink, showchecks=0), self.localize("Hide Checks"))
      else:
        checkslink = widgets.Link(self.makelink(baseindexlink, showchecks=1), self.localize("Show Checks"))
      actionlinks.append(checkslink)
    if "assign" in linksrequired and "translate" in self.rights:
      if self.showassigns:
        assignslink = widgets.Link(self.makelink(baseindexlink, showassigns=0), self.localize("Hide Assigns"))
      else:
        assignslink = widgets.Link(self.makelink(baseindexlink, showassigns=1), self.localize("Show Assigns"))
      actionlinks.append(assignslink)
    if "review" in linksrequired and projectstats.get("has-suggestion", 0):
      if "review" in self.rights:
        reviewlink = self.localize("Review Suggestions")
      else:
        reviewlink = self.localize("View Suggestions")
      reviewlink = widgets.Link(self.makelink(baseactionlink, review=1, **{"has-suggestion": 1}), reviewlink)
      actionlinks.append(reviewlink)
    if "quick" in linksrequired and projectstats.get("translated", 0) < projectstats.get("total", 0):
      if "translate" in self.rights:
        quicklink = self.localize("Quick Translate")
      else:
        quicklink = self.localize("View Untranslated")
      quicklink = widgets.Link(self.makelink(baseactionlink, fuzzy=1, blank=1), quicklink)
      actionlinks.append(quicklink)
    if "all" in linksrequired and "translate" in self.rights:
      translatelink = widgets.Link(self.makelink(baseactionlink), self.localize('Translate All'))
      actionlinks.append(translatelink)
    return actionlinks

  def getitemstats(self, basename, projectstats, numfiles):
    """returns a widget summarizing item statistics"""
    translated = projectstats.get("translated", 0)
    total = projectstats.get("total", 0)
    percentfinished = (translated*100/max(total, 1))
    if numfiles is None:
      statssummary = ""
    else:
      statssummary = self.localize("%d files, ") % numfiles
    statssummary += self.localize("%d/%d strings (%d%%) translated") % (translated, total, percentfinished)
    statsdetails = [statssummary]
    if not basename or basename.endswith("/"):
      linkbase = basename + "translate.html?"
    else:
      linkbase = basename + "?translate=1"
    if total and self.showchecks:
      statsdetails = statsdetails + self.getcheckdetails(projectstats, linkbase)
    if total and self.showtracks:
      trackfilter = (self.dirfilter or "") + basename
      trackpofilenames = self.project.browsefiles(trackfilter)
      projecttracks = self.project.gettracks(trackpofilenames)
      statsdetails += self.gettrackdetails(projecttracks, linkbase)
    if total and self.showassigns:
      if not basename or basename.endswith("/"):
        removelinkbase = "?showassigns=1&removeassigns=1"
      else:
        removelinkbase = "?showassigns=1&removeassigns=1&removefilter=%s" % basename
      statsdetails += self.getassigndetails(projectstats, linkbase, removelinkbase)
    statsdetails = widgets.SeparatedList(statsdetails, "<br/>\n")
    return pagelayout.ItemStatistics(statsdetails)

  def gettrackdetails(self, projecttracks, linkbase):
    """return a list of strings describing the results of tracks"""
    for trackmessage in projecttracks:
      yield widgets.Span(trackmessage, cls='trackerdetails')

  def getcheckdetails(self, projectstats, linkbase):
    """return a list of strings describing the results of checks"""
    total = max(projectstats.get("total", 0), 1)
    checklinks = []
    keys = projectstats.keys()
    keys.sort()
    for checkname in keys:
      if not checkname.startswith("check-"):
        continue
      checkcount = projectstats[checkname]
      checkname = checkname.replace("check-", "", 1)
      if total and checkcount:
        checklink = widgets.Link(self.makelink(linkbase, **{checkname:1}), checkname)
        stats = self.localize("%d strings (%d%%) failed") % (checkcount, (checkcount * 100 / total))
        checklinks += [[checklink, stats]]
    return checklinks

  def getassigndetails(self, projectstats, linkbase, removelinkbase):
    """return a list of strings describing the assigned strings"""
    total = max(projectstats.get("total", 0), 1)
    for assignname, assigncount in projectstats.iteritems():
      if not assignname.startswith("assign-"):
        continue
      assignname = assignname.replace("assign-", "", 1)
      if total and assigncount:
        assignlink = widgets.Link(self.makelink(linkbase, assignedto=assignname), assignname)
        stats = self.localize("%d strings (%d%%) assigned") % (assigncount, (assigncount * 100 / total))
        removetext = self.localize("Remove")
        removelink = widgets.Link(self.makelink(removelinkbase, assignedto=assignname), removetext)
        yield [assignlink, ": ", stats, " ", removelink]

