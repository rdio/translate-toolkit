#!/usr/bin/env python

from jToolkit.widgets import widgets
from jToolkit.widgets import table

class PootleSidebar(widgets.Division):
  """the bar at the side describing current login details etc"""
  def __init__(self, session):
    title = widgets.Division(session.instance.title, None, {"class":"sidetitle"})
    description = widgets.Division(session.instance.description, None, {"class":"side"})
    logintitle = widgets.Division("login status", None, {"class":"sidetitle"})
    if session.status:
      loginstatus = session.status
    else:
      loginstatus = "not logged in"
    loginstatus = widgets.Division(loginstatus, None, {"class":"side"})
    widgets.Division.__init__(self, [title, description, logintitle, loginstatus], "links")

class PootleBanner(widgets.Division):
  """the banner at the top"""
  def __init__(self, instance, maxheight=135):
    baseurl = instance.baseurl
    bannertable = table.TableLayout({"width":"100%", "cellpadding":0, "cellspacing":0, "border":0})
    width, height = min((180*maxheight/135, maxheight), (180, 135))
    pootleimage = widgets.Image(baseurl+"images/pootle.jpg", {"width":width, "height":height})
    pootlecell = table.TableCell(pootleimage, {"width": width, "align":"left", "valign":"top"})
    gapimage = widgets.Image(baseurl+"images/gap.gif", {"width":5, "height":5})
    gapcell = table.TableCell(gapimage, {"width":5})
    width, height = min((238*maxheight/81, 81), (238, 81))
    logoimage = widgets.Image(baseurl+"images/top.gif", {"width":width, "height":height})
    logocell = table.TableCell(logoimage, {"align":"center", "valign":"middle"})
    bordercell = table.TableCell([], {"class":"border_top", "align":"right", "valign":"middle"})
    toptable = table.TableLayout({"class":"header", "width":"100%", "height":maxheight, "cellpadding":0, "cellspacing":0, "border":0})
    toptable.setcell(0, 0, logocell)
    toptable.setcell(1, 0, bordercell)
    topcell = table.TableCell(toptable, {"width":"100%"})
    bannertable.setcell(0, 0, pootlecell)
    bannertable.setcell(0, 1, gapcell)
    bannertable.setcell(0, 2, topcell)
    widgets.Division.__init__(self, bannertable, id="banner")

class PootlePage(widgets.Page):
  """the main page"""
  def __init__(self, title, contents, session, bannerheight=135):
    stylesheets = [session.instance.baseurl + session.instance.stylesheet, session.instance.baseurl + "pootle.css"]
    self.banner = PootleBanner(session.instance, bannerheight)
    self.links = PootleSidebar(session)
    widgets.Page.__init__(self, title, [self.banner, contents, self.links], {"includeheading":False}, stylesheets=stylesheets)

