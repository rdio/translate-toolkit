#!/usr/bin/env python

from jToolkit.widgets import widgets
from jToolkit.widgets import table
from translate.pootle import pagelayout
from translate.pootle import projects

class TranslatePage(pagelayout.PootlePage):
  """the page which lets people edit translations"""
  def __init__(self, project, subproject, session, argdict, dirfilter=None):
    self.project = project
    self.subproject = subproject
    self.dirfilter = dirfilter
    self.translationproject = projects.getproject(self.subproject)
    self.matchnames = self.getmatchnames(argdict, self.translationproject.checker)
    self.translationsession = self.translationproject.gettranslationsession(session)
    self.instance = session.instance
    self.receivetranslations(argdict)
    translations = self.gettranslations()
    contextinfo = widgets.HiddenFieldList({"pofilename": self.pofilename})
    translateform = widgets.Form([translations, contextinfo], {"name": "translate", "action":""})
    title = "Pootle: translating %s into %s: %s" % (self.subproject.fullname, self.project.fullname, self.pofilename)
    translatediv = pagelayout.TranslateForm(translateform)
    pagelayout.PootlePage.__init__(self, title, translatediv, session, bannerheight=81)
    self.links.addcontents(pagelayout.SidebarTitle("current file"))
    self.links.addcontents(pagelayout.SidebarText(self.pofilename))
    if self.matchnames:
      checknames = [matchname.replace("check-", "", 1) for matchname in self.matchnames]
      self.links.addcontents(pagelayout.SidebarText("checking %s" % ", ".join(checknames)))
    self.links.addcontents(pagelayout.SidebarTitle("current folder"))
    if dirfilter is None:
      currentfolderlink = widgets.Link("index.html", "/")
    else:
      currentfolderlink = widgets.Link("index.html", dirfilter)
    self.links.addcontents(pagelayout.SidebarText(currentfolderlink))
    postats = self.translationproject.getpostats(self.pofilename)
    blank, fuzzy = postats["blank"], postats["fuzzy"]
    translated, total = postats["translated"], postats["total"]
    self.links.addcontents(pagelayout.SidebarText("%d/%d translated\n(%d blank, %d fuzzy)" % (translated, total, blank, fuzzy)))
    autoexpandscript = widgets.Script('text/javascript', '', newattribs={'src': self.instance.baseurl + 'js/autoexpand.js'})
    self.headerwidgets.append(autoexpandscript)

  def receivetranslations(self, argdict):
    """receive any translations submitted by the user"""
    skip = "skip" in argdict
    for key, value in argdict.iteritems():
      if key.startswith("trans"):
        try:
          item = int(key.replace("trans",""))
        except:
          continue
        # submit the actual translation back to the project...
        pofilename = argdict["pofilename"]
	if skip:
          self.translationsession.skiptranslation(pofilename, item)
	else:
          self.translationsession.receivetranslation(pofilename, item, value)

  def getmatchnames(self, argdict, checker): 
    """returns any checker filters the user has asked to match..."""
    matchnames = []
    for checkname in argdict:
      if checkname in checker.getfilters():
        matchnames.append("check-" + checkname)
      if checkname in ["fuzzy", "blank", "translated"]:
        matchnames.append(checkname)
    return matchnames

  def addtransrow(self, rownum, origcell, transcell):
    self.transtable.setcell(rownum, 0, origcell)
    self.transtable.setcell(rownum, 1, transcell)

  def gettranslations(self):
    self.transtable = table.TableLayout({"class":"translate-table", "cellpadding":10})
    origtitle = table.TableCell("original", {"class":"translate-table-title"})
    transtitle = table.TableCell("translation", {"class":"translate-table-title"})
    self.addtransrow(-1, origtitle, transtitle)
    self.pofilename, item, theorig, thetrans = self.translationsession.getnextitem(self.dirfilter, self.matchnames)
    translationsbefore = self.translationproject.getitemsbefore(self.pofilename, item, 3)
    translationsafter = self.translationproject.getitemsafter(self.pofilename, item, 3)
    self.translations = translationsbefore + [(theorig, thetrans)] + translationsafter
    self.textcolors = ["#000000", "#000060"]
    for row, (orig, trans) in enumerate(self.translations):
      thisitem = item - len(translationsbefore) + row
      self.addtranslationrow(thisitem, orig, trans, thisitem == item)
    self.transtable.shrinkrange()
    return self.transtable

  def getorigcell(self, row, orig, editable):
    origclass = "translate-original "
    if editable:
      origclass += "translate-original-focus "
    else:
      origclass += "autoexpand "
    origdiv = widgets.Division([], "orig%d" % row, cls=origclass)
    origtext = widgets.Font(orig, {"color":self.textcolors[row % 2]})
    origdiv.addcontents(origtext)
    return table.TableCell(origdiv, {"class":"translate-original"})

  def gettranscell(self, row, trans, editable):
    transclass = "translate-translation "
    if not editable:
      transclass += "autoexpand "
    transdiv = widgets.Division([], "trans%d" % row, cls=transclass)
    if editable:
      if isinstance(trans, str):
        trans = trans.decode("utf8")
      textarea = widgets.TextArea({"name":"trans%d" % row, "rows":3, "cols":40}, contents=trans)
      skipbutton = widgets.Input({"type":"submit", "name":"skip", "value":"skip"}, "skip")
      submitbutton = widgets.Input({"type":"submit", "name":"submit", "value":"submit"}, "submit")
      contents = [textarea, skipbutton, submitbutton]
    else:
      contents = widgets.Font(trans, {"color":self.textcolors[row % 2]})
    transdiv.addcontents(contents)
    return table.TableCell(transdiv, {"class":"translate-translation"})

  def addtranslationrow(self, row, orig, trans, editable=False):
    """returns an origcell and a transcell for displaying a translation"""
    origcell = self.getorigcell(row, orig, editable)
    transcell = self.gettranscell(row, trans, editable)
    self.addtransrow(row, origcell, transcell)

