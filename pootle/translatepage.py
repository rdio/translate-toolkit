#!/usr/bin/env python

from jToolkit.widgets import widgets
from jToolkit.widgets import table
from translate.pootle import pagelayout
from translate.pootle import projects

class TranslatePage(pagelayout.PootlePage):
  """the page which lets people edit translations"""
  def __init__(self, project, subproject, session, argdict):
    self.project = project
    self.subproject = subproject
    self.translationproject = projects.getproject(self.subproject)
    self.translationsession = self.translationproject.gettranslationsession(session)
    for key, value in argdict.iteritems():
      if key.startswith("trans"):
        try:
          item = int(key.replace("trans",""))
        except:
          continue
        # submit the actual translation back to the project...
        pofilename = argdict["pofilename"]
        self.translationsession.receivetranslation(pofilename, item, value)
    self.instance = session.instance
    translations = self.gettranslations()
    contextinfo = widgets.HiddenFieldList({"pofilename": self.pofilename})
    translateform = widgets.Form([translations, contextinfo], {"name": "translate", "action":""})
    title = "Pootle: translating %s into %s: %s" % (self.subproject.fullname, self.project.fullname, self.pofilename)
    translatediv = pagelayout.TranslateForm(translateform)
    contents = widgets.Division([translatediv], "content")
    pagelayout.PootlePage.__init__(self, title, contents, session, bannerheight=81)
    self.links.addcontents(pagelayout.SidebarTitle("current file"))
    self.links.addcontents(pagelayout.SidebarText(self.pofilename))
    postats = self.translationproject.getpostats(self.pofilename)
    blank, fuzzy = postats["blank"], postats["fuzzy"]
    translated, total = postats["translated"], postats["total"]
    self.links.addcontents(pagelayout.SidebarText("%d/%d translated\n(%d blank, %d fuzzy)" % (translated, total, blank, fuzzy)))
    autoexpandscript = widgets.Script('text/javascript', '', newattribs={'src': self.instance.baseurl + 'js/autoexpand.js'})
    self.headerwidgets.append(autoexpandscript)

  def addtransrow(self, rownum, origcell, transcell):
    self.transtable.setcell(rownum, 0, origcell)
    self.transtable.setcell(rownum, 1, transcell)

  def gettranslations(self):
    self.transtable = table.TableLayout({"class":"translate-table", "cellpadding":10})
    origtitle = table.TableCell("original", {"class":"translate-table-title"})
    transtitle = table.TableCell("translation", {"class":"translate-table-title"})
    self.addtransrow(-1, origtitle, transtitle)
    self.pofilename, item, theorig, thetrans = self.translationsession.getnextitem()
    translationsbefore = self.translationproject.getitemsbefore(self.pofilename, item, 3)
    translationsafter = self.translationproject.getitemsafter(self.pofilename, item, 3)
    self.textcolors = ["#000000", "#000060"]
    for row, (orig, trans) in enumerate(translationsbefore):
      self.addtranslationrow(item - len(translationsbefore) + row, orig, trans)
    self.addtranslationrow(item, theorig, thetrans, True)
    for row, (orig, trans) in enumerate(translationsafter):
      self.addtranslationrow(item + 1 + row, orig, trans)
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
      submitbutton = widgets.Input({"type":"submit", "name":"submit", "value":"submit"}, "submit")
      contents = [textarea, submitbutton]
    else:
      contents = widgets.Font(trans, {"color":self.textcolors[row % 2]})
    transdiv.addcontents(contents)
    return table.TableCell(transdiv, {"class":"translate-translation"})

  def addtranslationrow(self, row, orig, trans, editable=False):
    """returns an origcell and a transcell for displaying a translation"""
    origcell = self.getorigcell(row, orig, editable)
    transcell = self.gettranscell(row, trans, editable)
    self.addtransrow(row, origcell, transcell)

