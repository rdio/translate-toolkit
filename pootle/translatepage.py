#!/usr/bin/env python

from jToolkit.widgets import widgets
from jToolkit.widgets import table
from translate.pootle import pagelayout
from translate.storage import po

class TranslationIterator:
  def __init__(self, project, subproject):
    inputfile = open(subproject.pofile, "r")
    self.pofile = po.pofile(inputfile)
    self.translations = [(po.getunquotedstr(thepo.msgid), po.getunquotedstr(thepo.msgstr)) for thepo in self.pofile.poelements if not thepo.isheader()]
    self.item = 0

  def gettranslations(self, contextbefore=3, contextafter=3):
    """returns (a set of translations before, the next translation, a set of translations after)"""
    return self.translations[min(self.item-contextbefore,0):self.item], self.translations[self.item], self.translations[self.item+1:self.item+1+contextafter]

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
    rowoffset += len(translationsbefore)
    orig, trans = currenttranslation
    self.addtranslationrow(rowoffset, orig, trans, True)
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

