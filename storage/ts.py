#!/usr/bin/env python
#
# Copyright 2002-2004 Zuza Software Foundation
# 
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""module for parsing Qt .ts files for translation"""

from xml.dom import minidom


class QtTsParser:
  def __init__(self, inputfile=None):
    """make a new QtTsParser, reading from the given inputfile if required"""
    self.filename = getattr(inputfile, "filename", None)
    if inputfile is not None:
      self.document = minidom.parse(inputfile)
      assert self.document.documentElement.tagName == "TS"

  def getnodetext(self, node):
    """returns the node's text by iterating through the child nodes"""
    return "".join([t.data for t in node.childNodes if t.nodeType == t.TEXT_NODE])

  def getcontextname(self, contextnode):
    """returns the name of the given context"""
    namenodes = contextnode.getElementsByTagName("name")
    if not namenodes:
      return None
    return self.getnodetext(namenodes[0])

  def getcontextnode(self, contextname):
    """finds the contextnode with the given name"""
    contextnodes = self.document.getElementsByTagName("context")
    for contextnode in contextnodes:
      if self.getcontextname(contextnode) == contextname:
        return contextnode
    return None

  def getmessagenodes(self, context=None):
    """returns all the messagenodes, limiting to the given context (name or node) if given"""
    if context is None:
      return self.document.getElementsByTagName("message")
    else:
      if isinstance(context, (str, unicode)):
        # look up the context node by name
        context = self.getcontextnode(context)
        if context is None:
          return []
      return context.getElementsByTagName("message")

  def getmessagesource(self, message):
    """returns the message source for a given node"""
    sourcenode = message.getElementsByTagName("source")[0]
    return self.getnodetext(sourcenode)

  def getmessagetranslation(self, message):
    """returns the message translation for a given node"""
    sourcenode = message.getElementsByTagName("translation")[0]
    return self.getnodetext(sourcenode)

  def iteritems(self):
    """iterates through (contextname, messages)"""
    for contextnode in self.document.getElementsByTagName("context"):
      yield self.getcontextname(contextnode), self.getmessagenodes(contextnode)

  def __del__(self):
    """clean up the document if required"""
    if hasattr(self, "document"):
      self.document.unlink()

