#!/usr/bin/env python

from jToolkit.web import server
from jToolkit.widgets import widgets
from translate.pootle import indexpage
from translate.pootle import translatepage

class PootleServer(server.AppServer):
  """the Server that serves the Pootle Pages"""
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
      return indexpage.PootleIndex(session)
    elif hasattr(session.instance.projects, top):
      project = getattr(session.instance.projects, top)
      pathwords = pathwords[1:]
      if pathwords:
        top = pathwords[0]
      else:
        top = ""
      if not top or top == "index.html":
        return indexpage.ProjectIndex(project, session)
      if hasattr(project.subprojects, top):
        subproject = getattr(project.subprojects, top)
        pathwords = pathwords[1:]
        if pathwords:
          top = pathwords[0]
        else:
          top = ""
        if not top or top == "index.html":
          return translatepage.TranslatePage(project, subproject, session, argdict)
    elif top == "test.html":
      contents = repr(session.status)
      page = widgets.PlainContents(contents)
      page.content_type = "text/plain"
      return page
    return None

