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

