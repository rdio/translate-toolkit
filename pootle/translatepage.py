#!/usr/bin/env python

from jToolkit.widgets import widgets
from jToolkit.widgets import table
from translate.pootle import pagelayout
from translate.pootle import projects
import difflib

class TranslatePage(pagelayout.PootlePage):
  """the page which lets people edit translations"""
  def __init__(self, project, session, argdict, dirfilter=None):
    self.argdict = argdict
    self.dirfilter = dirfilter
    self.project = project
    self.matchnames = self.getmatchnames(self.project.checker)
    self.searchtext = self.argdict.get("searchtext", "")
    # TODO: fix this in jToolkit
    if isinstance(self.searchtext, unicode):
      self.searchtext = self.searchtext.encode("utf8")
    self.session = self.project.gettranslationsession(session)
    self.rights = self.session.getrights()
    self.instance = session.instance
    self.pofilename = None
    self.lastitem = None
    self.receivetranslations()
    # TODO: clean up modes to be one variable
    self.viewmode = self.argdict.get("view", 0) and "view" in self.rights
    self.reviewmode = self.argdict.get("review", 0)
    if not self.viewmode and not self.reviewmode:
      if not "translate" in self.rights:
        if "view" in self.rights:
          self.viewmode = True
    self.finditem()
    self.maketable()
    searchcontextinfo = widgets.HiddenFieldList({"searchtext": self.searchtext})
    contextinfo = widgets.HiddenFieldList({"pofilename": self.pofilename})
    translateform = widgets.Form([self.transtable, searchcontextinfo, contextinfo], {"name": "translate", "action":""})
    title = "Pootle: translating %s into %s: %s" % (self.project.projectname, self.project.languagename, self.pofilename)
    if self.viewmode:
      pagelinks = []
      if self.firstitem > 0:
        linkitem = max(self.firstitem - 10, 0)
        pagelinks.append(widgets.Link("?translate=1&view=1&item=%d" % linkitem, "Previous %d" % (self.firstitem - linkitem)))
      if self.firstitem + len(self.translations) < self.project.getpofilelen(self.pofilename):
        linkitem = self.firstitem + 10
        itemcount = min(self.project.getpofilelen(self.pofilename) - linkitem, 10)
        pagelinks.append(widgets.Link("?translate=1&view=1&item=%d" % linkitem, "Next %d" % itemcount))
      pagelinks = pagelayout.IntroText(pagelinks)
    else:
      pagelinks = []
    translatediv = pagelayout.TranslateForm([pagelinks, translateform])
    pagelayout.PootlePage.__init__(self, title, translatediv, session, bannerheight=81)
    self.addfilelinks(self.pofilename, self.matchnames)
    if dirfilter and dirfilter.endswith(".po"):
      currentfolder = "/".join(dirfilter.split("/")[:-1])
    else:
      currentfolder = dirfilter
    self.addfolderlinks("current folder", currentfolder, "index.html")
    autoexpandscript = widgets.Script('text/javascript', '', newattribs={'src': self.instance.baseurl + 'js/autoexpand.js'})
    self.headerwidgets.append(autoexpandscript)

  def addfilelinks(self, pofilename, matchnames):
    """adds a section on the current file, including any checks happening"""
    searchcontextinfo = widgets.HiddenFieldList({"pofilename": self.pofilename})
    self.addsearchbox(self.searchtext, searchcontextinfo)
    self.links.addcontents(pagelayout.SidebarTitle("current file"))
    self.links.addcontents(pagelayout.SidebarText(pofilename))
    if matchnames:
      checknames = [matchname.replace("check-", "", 1) for matchname in matchnames]
      self.links.addcontents(pagelayout.SidebarText("checking %s" % ", ".join(checknames)))
    postats = self.project.getpostats(self.pofilename)
    blank, fuzzy = postats["blank"], postats["fuzzy"]
    translated, total = postats["translated"], postats["total"]
    self.links.addcontents(pagelayout.SidebarText("%d/%d translated\n(%d blank, %d fuzzy)" % (translated, total, blank, fuzzy)))

  def receivetranslations(self):
    """receive any translations submitted by the user"""
    self.pofilename = self.argdict.get("pofilename", None)
    if self.pofilename is None:
      return
    skips = []
    submitsuggests = []
    submits = []
    accepts = []
    rejects = []
    translations = {}
    suggestions = {}
    def getitem(key, prefix):
      if not key.startswith(prefix):
        return None
      try:
        return int(key.replace(prefix, "", 1))
      except:
        return None
    def getpointitem(key, prefix):
      if not key.startswith(prefix):
        return None, None
      try:
        key = key.replace(prefix, "", 1)
        item, suggid = key.split(".", 1)
        return int(item), int(suggid)
      except:
        return None, None
    for key, value in self.argdict.iteritems():
      item = getitem(key, "skip")
      if item is not None:
        skips.append(item)
      item = getitem(key, "submitsuggest")
      if item is not None:
        submitsuggests.append(item)
      item = getitem(key, "submit")
      if item is not None:
        submits.append(item)
      item, suggid = getpointitem(key, "accept")
      if item is not None:
        accepts.append((item, suggid))
      item, suggid = getpointitem(key, "reject")
      if item is not None:
        rejects.append((item, suggid))
      item = getitem(key, "trans")
      if item is not None:
        translations[item] = value
      item, suggid = getpointitem(key, "sugg")
      if item is not None:
        suggestions[item, suggid] = value
    for item in skips:
      self.session.skiptranslation(self.pofilename, item)
      self.lastitem = item
    for item in submitsuggests:
      if item in skips or item not in translations:
        continue
      value = translations[item]
      self.session.receivetranslation(self.pofilename, item, value, True)
      self.lastitem = item
    for item in submits:
      if item in skips or item not in translations:
        continue
      value = translations[item]
      self.session.receivetranslation(self.pofilename, item, value, False)
      self.lastitem = item
    for item, suggid in rejects:
      value = suggestions[item, suggid]
      self.project.rejectsuggestion(self.pofilename, item, suggid, value)
      self.lastitem = item
    for item, suggid in accepts:
      if (item, suggid) in rejects or (item, suggid) not in suggestions:
        continue
      value = suggestions[item, suggid]
      self.project.acceptsuggestion(self.pofilename, item, suggid, value)
      self.lastitem = item

  def getmatchnames(self, checker): 
    """returns any checker filters the user has asked to match..."""
    matchnames = []
    for checkname in self.argdict:
      if checkname in ["fuzzy", "blank", "translated", "has-suggestion"]:
        matchnames.append(checkname)
      elif checkname in checker.getfilters():
        matchnames.append("check-" + checkname)
    matchnames.sort()
    return matchnames

  def finditem(self):
    """finds the focussed item for this page, searching as neccessary"""
    item = self.argdict.get("item", None)
    if item is None:
      try:
        search = projects.Search(dirfilter=self.dirfilter, matchnames=self.matchnames, searchtext=self.searchtext)
        if self.session.session.isopen:
          search.assignedto = self.session.session.username
          if self.reviewmode:
            search.assignedaction = "review"
          elif not self.viewmode:
            search.assignedaction = "suggest"
        self.pofilename, self.item = self.project.searchpoitems(self.pofilename, self.lastitem, search).next()
      except StopIteration:
        if self.lastitem is None:
          raise StopIteration("There are no items matching that search")
        else:
          raise StopIteration("You have finished going through the items you selected")
    else:
      if not item.isdigit():
        raise ValueError("Invalid item given")
      self.item = int(item)
      self.pofilename = self.argdict.get("pofilename", self.dirfilter)

  def gettranslations(self):
    """gets the list of translations desired for the view, and sets editable and firstitem parameters"""
    if self.viewmode:
      self.editable = []
      self.firstitem = self.item
      return self.project.getitems(self.pofilename, self.item, self.item+10)
    else:
      self.editable = [self.item]
      self.firstitem = max(self.item - 3, 0)
      return self.project.getitems(self.pofilename, self.item-3, self.item+4)

  def maketable(self):
    self.translations = self.gettranslations()
    if self.reviewmode:
      suggestions = {self.item: self.project.getsuggestions(self.pofilename, self.item)}
    self.transtable = table.TableLayout({"class":"translate-table", "cellpadding":10})
    origtitle = table.TableCell("original", {"class":"translate-table-title"})
    transtitle = table.TableCell("translation", {"class":"translate-table-title"})
    self.transtable.setcell(-1, 0, origtitle)
    self.transtable.setcell(-1, 1, transtitle)
    self.textcolors = ["#000000", "#000060"]
    for row, (orig, trans) in enumerate(self.translations):
      item = self.firstitem + row
      itemclasses = self.project.getitemclasses(self.pofilename, item)
      origdiv = self.getorigdiv(item, orig, item in self.editable, itemclasses)
      if item in self.editable:
        if self.reviewmode:
          transdiv = self.gettransreview(item, trans, suggestions[item])
        else:
          transdiv = self.gettransedit(item, trans)
      else:
        transdiv = self.gettransview(item, trans)
      origcell = table.TableCell(origdiv, {"class":"translate-original"})
      self.transtable.setcell(row, 0, origcell)
      transcell = table.TableCell(transdiv, {"class":"translate-translation"})
      self.transtable.setcell(row, 1, transcell)
      if item in self.editable:
        origcell.attribs["class"] += " translate-focus"
        transcell.attribs["class"] += " translate-focus"
    self.transtable.shrinkrange()
    return self.transtable

  def getorigdiv(self, item, orig, editable, itemclasses):
    origclass = "translate-original "
    if editable:
      origclass += "translate-original-focus "
    else:
      origclass += "autoexpand "
    origdiv = widgets.Division([], "orig%d" % item, cls=origclass)
    origtext = widgets.Font(orig, {"color":self.textcolors[item % 2]})
    if itemclasses:
      origtext = widgets.Tooltip(" ".join(itemclasses), origtext)
    origdiv.addcontents(origtext)
    return origdiv

  def geteditlink(self, item):
    """gets a link to edit the given item, if the user has permission"""
    if "translate" in self.rights or "suggest" in self.rights:
      return pagelayout.TranslateActionLink("?translate=1&item=%d&pofilename=%s" % (item, self.pofilename), "Edit", "editlink%d" % item)
    else:
      return ""

  def gettransbuttons(self, item, desiredbuttons=["skip", "suggest", "translate"]):
    """gets buttons for actions on translation"""
    buttons = []
    if "skip" in desiredbuttons:
      skipbutton = widgets.Input({"type":"submit", "name":"skip%d" % item, "value":"skip"}, "skip")
      buttons.append(skipbutton)
    if "suggest" in desiredbuttons and "suggest" in self.rights:
      suggestbutton = widgets.Input({"type":"submit", "name":"submitsuggest%d" % item, "value":"suggest"}, "suggest")
      buttons.append(suggestbutton)
    if "translate" in desiredbuttons and "translate" in self.rights:
      submitbutton = widgets.Input({"type":"submit", "name":"submit%d" % item, "value":"submit"}, "submit")
      buttons.append(submitbutton)
    return buttons

  def gettransedit(self, item, trans):
    """returns a widget for editing the given item and translation"""
    if isinstance(trans, str):
      trans = trans.decode("utf8")
    textarea = widgets.TextArea({"name":"trans%d" % item, "rows":3, "cols":40}, contents=trans)
    buttons = self.gettransbuttons(item)
    transdiv = widgets.Division([textarea, buttons], "trans%d" % item, cls="translate-translation")
    return transdiv

  def highlightdiffs(self, text, diffs, issrc=True):
    """highlights the differences in diffs in the text.
    diffs should be list of diff opcodes
    issrc specifies whether to use the src or destination positions in reconstructing the text"""
    if issrc:
      diffstart = [(i1, 'start', tag) for (tag, i1, i2, j1, j2) in diffs if tag != 'equal']
      diffstop = [(i2, 'stop', tag) for (tag, i1, i2, j1, j2) in diffs if tag != 'equal']
    else:
      diffstart = [(j1, 'start', tag) for (tag, i1, i2, j1, j2) in diffs if tag != 'equal']
      diffstop = [(j2, 'stop', tag) for (tag, i1, i2, j1, j2) in diffs if tag != 'equal']
    diffswitches = diffstart + diffstop
    diffswitches.sort()
    textdiff = ""
    textnest = 0
    textpos = 0
    for i, switch, tag in diffswitches:
      textdiff += text[textpos:i]
      if switch == 'start':
        textnest += 1
      elif switch == 'stop':
        textnest -= 1
      if switch == 'start' and textnest == 1:
        # start of a textition
        textdiff += "<span style='background-color: #ffff00'>"
      elif switch == 'stop' and textnest == 0:
        # start of an equals block
        textdiff += "</span>"
      textpos = i
    textdiff += text[textpos:]
    return textdiff

  def gettransreview(self, item, trans, suggestions):
    """returns a widget for reviewing the given item's suggestions"""
    if isinstance(trans, str):
      trans = trans.decode("utf8")
    currenttitle = widgets.Division("<b>Current Translation:</b>")
    diffcodes = [difflib.SequenceMatcher(None, trans, suggestion).get_opcodes() for suggestion in suggestions]
    combineddiffs = reduce(list.__add__, diffcodes)
    transdiff = self.highlightdiffs(trans, combineddiffs, issrc=True)
    editlink = self.geteditlink(item)
    currenttext = pagelayout.TranslationText([editlink, widgets.Font(transdiff, {"color":self.textcolors[item % 2]})])
    suggdivs = []
    for suggid, suggestion in enumerate(suggestions):
      suggdiffcodes = diffcodes[suggid]
      suggdiff = self.highlightdiffs(suggestion, suggdiffcodes, issrc=False)
      suggestedby = self.project.getsuggester(self.pofilename, item, suggid)
      if isinstance(suggestion, str):
        suggestion = suggestion.decode("utf8")
      if len(suggestions) > 1:
        if suggestedby:
          suggtitle = "Suggestion %d by %s:" % (suggid+1, suggestedby)
        else:
          suggtitle = "Suggestion %d:" % (suggid+1)
      else:
        if suggestedby:
          suggtitle = "Suggestion by %s:" % (suggestedby)
        else:
          suggtitle = "Suggestion:"
      suggtitle = widgets.Division("<b>%s</b>" % suggtitle)
      suggestiontext = pagelayout.TranslationText(widgets.Font(suggdiff, {"color":self.textcolors[item % 2]}))
      suggestionhidden = widgets.Input({'type': 'hidden', "name": "sugg%d.%d" % (item, suggid), 'value': suggestion})
      if "review" in self.rights:
        acceptbutton = widgets.Input({"type":"submit", "name":"accept%d.%d" % (item, suggid), "value":"accept"}, "accept")
        rejectbutton = widgets.Input({"type":"submit", "name":"reject%d.%d" % (item, suggid), "value":"reject"}, "reject")
        buttons = [acceptbutton, rejectbutton]
      else:
        buttons = []
      suggdiv = widgets.Division(["<br/>", suggtitle, suggestiontext, suggestionhidden, "<br/>", buttons], "sugg%d" % item)
      suggdivs.append(suggdiv)
    transbuttons = self.gettransbuttons(item, ["skip"])
    if suggdivs:
      suggdivs[-1].addcontents(transbuttons)
    else:
      suggdivs.append(transbuttons)
    transdiv = widgets.Division([currenttitle, currenttext] + suggdivs, "trans%d" % item, cls="translate-translation")
    return transdiv

  def gettransview(self, item, trans):
    """returns a widget for viewing the given item's translation"""
    editlink = self.geteditlink(item)
    text = pagelayout.TranslationText([editlink, widgets.Font(trans, {"color":self.textcolors[item % 2]})])
    transdiv = widgets.Division(text, "trans%d" % item, cls="translate-translation autoexpand")
    return transdiv

