#!/usr/bin/env python

from jToolkit.widgets import widgets
from jToolkit.widgets import table
from translate.pootle import pagelayout

dummytranslations = [
  ("Important Information for Arabic and Hebrew Versions", "Impurtunt Inffurmeshun fur Erebeec und Hebroo Ferseeuns"),
  ("If the user interface of the Arabic or Hebrew versions shows blanks or squares instead of text, please install the most recent Java Runtime Environment (JRE 1.4.1) before running the OpenOffice.org Installation Program. The JRE will install the fonts required for Arabic and Hebrew versions.", "Iff zee user interffece-a ooff zee Erebeec oor Hebroo ferseeuns shoos blunks oor sqooeres insteed ooff text, pleese-a instell zee must recent Jefa Roonteeme-a Infurunment (JRE 1.4.1) beffure-a roonneeng zee OopenOffffeece-a.oorg Instelleshun Prugrem. Zee JRE veell instell zee funts reqooured fur Erebeec und Hebroo ferseeuns."),
  ("Important Information for Asian Versions", "Impurtunt Inffurmeshun fur Eseeun Ferseeuns"),
  ("Please change the following lines in your user environment settings before running the application.", "Pleese-a chunge-a zee fullooeeng leenes in yuoor user infurunment setteengs beffure-a roonneeng zee eppleeceshun. Bork Bork Bork!"),
  ("to (or add the following lines if they do not exist at all):", ""),
  ("Deinstalling a Network Installation Under Common Desktop Environment (CDE)", ""),
  ("The shortcuts set in the CDE in a network installation are not automatically removed during deinstallation. Before deinstallation, enter as Administrator (root) the following command line to remove the shortcuts from the CDE: /usr/dt/bin/dtappintegrate -u -s [path to OpenOffice.org].", "")
  ]

class TranslationIterator:
  def __init__(self, project, subproject):
    self.translations = dummytranslations

  def gettranslations(self, contextbefore=3, contextafter=3):
    """returns (a set of translations before, the next translation, a set of translations after)"""
    import random
    random.shuffle(self.translations)
    return self.translations[0:3], self.translations[3], self.translations[4:]

translationiterators = {}

class TranslatePage(pagelayout.PootlePage):
  """the main page"""
  def __init__(self, project, subproject, session):
    self.project = project
    self.subproject = subproject
    if (self.project, self.subproject) not in translationiterators:
      translationiterators[self.project, self.subproject] = TranslationIterator(self.project, self.subproject)
    self.translationiterator = translationiterators[self.project, self.subproject]
    self.instance = session.instance
    title = "Pootle: translating %s into %s" % (self.subproject.fullname, self.project.fullname)
    translateform = widgets.Form(self.gettranslations(), {"name": "translate", "action":""})
    divstyle = {"font-family": "verdana, arial, sans-serif", "font-size": "small", "line-height": "100%"}
    translatediv = widgets.Division(translateform, None, {"style": divstyle})
    contents = widgets.Division([translatediv], "content")
    pagelayout.PootlePage.__init__(self, title, contents, session, bannerheight=81)
    autoexpandscript = widgets.Script('text/javascript', '', newattribs={'src': self.instance.baseurl + 'js/autoexpand.js'})
    self.headerwidgets.append(autoexpandscript)

  def addtransrow(self, rownum, origcell, transcell):
    self.transtable.setcell(rownum, 0, origcell)
    self.transtable.setcell(rownum, 1, transcell)

  def gettranslations(self):
    self.transtable = table.TableLayout({"width":"100%", "cellpadding":10, "cellspacing":1, "border":0})
    origtitle = table.TableCell("<b>original</b>")
    transtitle = table.TableCell("<b>translation</b>")
    self.addtransrow(-1, origtitle, transtitle)
    translationsbefore, currenttranslation, translationsafter = self.translationiterator.gettranslations()
    self.textcolors = ["#000000", "#000060"]
    rowoffset = 0
    for row, (orig, trans) in enumerate(translationsbefore):
      self.addtranslationrow(rowoffset + row, orig, trans)
    rowoffset += row
    orig, trans = currenttranslation
    self.addtranslationrow(row, orig, trans, True)
    rowoffset += 1
    for row, (orig, trans) in enumerate(translationsafter):
      self.addtranslationrow(rowoffset + row, orig, trans)
    return self.transtable

  def getorigcell(self, row, orig, editable):
    origdiv = widgets.Division([], "orig%d" % row)
    if editable:
      orig = "<b>%s</b>" % orig
    else:
      origdiv.attribs["class"] = "autoexpand"
    origtext = widgets.Font(orig, {"color":self.textcolors[row % 2]})
    origdiv.addcontents(origtext)
    return table.TableCell(origdiv, {"bgcolor":"#e0e0e0", "width":"50%"})

  def gettranscell(self, row, trans, editable):
    transdiv = widgets.Division([], "trans%d" % row)
    if editable:
      textarea = widgets.TextArea({"name":"trans%d" % row, "rows":3, "cols":40}, contents=trans)
      submitbutton = widgets.Input({"type":"submit", "name":"submit", "value":"submit"}, "submit")
      contents = [textarea, submitbutton]
    else:
      contents = widgets.Font(trans, {"color":self.textcolors[row % 2]})
      transdiv.attribs["class"] = "autoexpand"
    transdiv.addcontents(contents)
    return table.TableCell(transdiv, {"width":"50%"})

  def addtranslationrow(self, row, orig, trans, editable=False):
    """returns an origcell and a transcell for displaying a translation"""
    origcell = self.getorigcell(row, orig, editable)
    transcell = self.gettranscell(row, trans, editable)
    self.addtransrow(row, origcell, transcell)

