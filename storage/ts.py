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

def writexml(self, writer, indent="", addindent="", newl=""):
    """a replacement to writexml that formats it more like typical .ts files"""
    # indent = current indentation
    # addindent = indentation to add to higher levels
    # newl = newline string
    writer.write(indent+"<" + self.tagName)

    attrs = self._get_attributes()
    a_names = attrs.keys()
    a_names.sort()

    for a_name in a_names:
        writer.write(" %s=\"" % a_name)
        minidom._write_data(writer, attrs[a_name].value)
        writer.write("\"")
    if self.childNodes:
        if len(self.childNodes) == 1 and self.childNodes[0].nodeType == self.TEXT_NODE:
          writer.write(">")
          for node in self.childNodes:
              node.writexml(writer,"","","")
          writer.write("</%s>%s" % (self.tagName,newl))
        else:
          writer.write(">%s"%(newl))
          for node in self.childNodes:
              node.writexml(writer,indent+addindent,addindent,newl)
          writer.write("%s</%s>%s" % (indent,self.tagName,newl))
    else:
        writer.write("/>%s"%(newl))

Element_writexml = minidom.Element.writexml
for elementclassname in dir(minidom):
  elementclass = getattr(minidom, elementclassname)
  if not isinstance(elementclass, type(minidom.Element)):
    continue
  if not issubclass(elementclass, minidom.Element):
    continue
  if elementclass.writexml != Element_writexml:
    continue
  elementclass.writexml = writexml

def _get_elements_by_tagName_faster_helper(parent, name, rc):
    for node in parent.childNodes:
        if node.nodeType == minidom.Node.ELEMENT_NODE and \
            (name == "*" or node.tagName == name):
            yield node
        for node in _get_elements_by_tagName_faster_helper(node, name, rc):
            yield node

def _get_elements_by_tagName_clever_helper(parent, name, onlysearch):
    """limits the search to within tags occuring in onlysearch"""
    for node in parent.childNodes:
        if node.nodeType == minidom.Node.ELEMENT_NODE and \
            (name == "*" or node.tagName == name):
            yield node
        if node.nodeType == minidom.Node.ELEMENT_NODE and node.tagName in onlysearch:
            for node in _get_elements_by_tagName_clever_helper(node, name, onlysearch):
                yield node

minidom._get_elements_by_tagName_helper = _get_elements_by_tagName_faster_helper
minidom.Document.searchElementsByTagName = _get_elements_by_tagName_clever_helper
minidom.Element.searchElementsByTagName = _get_elements_by_tagName_clever_helper

def getFirstElementByTagName(node, name):
  results = node.getElementsByTagName(name)
  if isinstance(results, list):
    return results[0]
  try:
    return results.next()
  except StopIteration:
    return None

def getnodetext(node):
  """returns the node's text by iterating through the child nodes"""
  if node is None: return ""
  return "".join([t.data for t in node.childNodes if t.nodeType == t.TEXT_NODE])

class QtTsParser:
  contextancestors = dict.fromkeys(["TS"])
  messageancestors = dict.fromkeys(["TS", "context"])
  def __init__(self, inputfile=None):
    """make a new QtTsParser, reading from the given inputfile if required"""
    self.filename = getattr(inputfile, "filename", None)
    self.knowncontextnodes = {}
    if inputfile is None:
      self.document = minidom.parseString("<!DOCTYPE TS><TS></TS>")
    else:
      self.document = minidom.parse(inputfile)
      assert self.document.documentElement.tagName == "TS"

  def addtranslation(self, contextname, source, translation, comment=None, transtype=None, createifmissing=False):
    """adds the given translation (will create the nodes required if asked). Returns success"""
    contextnode = self.getcontextnode(contextname)
    if contextnode is None:
      if not createifmissing:
        return False
      # construct a context node with the given name
      contextnode = self.document.createElement("context")
      namenode = self.document.createElement("name")
      nametext = self.document.createTextNode(contextname)
      namenode.appendChild(nametext)
      contextnode.appendChild(namenode)
      self.document.documentElement.appendChild(contextnode)
    for message in self.getmessagenodes(contextnode):
      if self.getmessagesource(message).strip() == source.strip():
        translationnode = getFirstElementByTagName(message, "translation")
        newtranslationnode = self.document.createElement("translation")
        translationtext = self.document.createTextNode(translation)
        newtranslationnode.appendChild(translationtext)
        message.replaceChild(newtranslationnode, translationnode)
        return True
    if not createifmissing:
      return False
    messagenode = self.document.createElement("message")
    sourcenode = self.document.createElement("source")
    sourcetext = self.document.createTextNode(source)
    sourcenode.appendChild(sourcetext)
    messagenode.appendChild(sourcenode)
    if comment:
        commentnode = self.document.createElement("comment")
        commenttext = self.document.createTextNode(comment)
        commentnode.appendChild(commenttext)
        messagenode.appendChild(commentnode)
    translationnode = self.document.createElement("translation")
    translationtext = self.document.createTextNode(translation)
    translationnode.appendChild(translationtext)
    if transtype:
      translationnode.setAttribute("type",transtype)
    messagenode.appendChild(translationnode)
    contextnode.appendChild(messagenode)
    return True

  def getxml(self):
    """return the ts file as xml"""
    xml = self.document.toprettyxml(indent="    ", encoding="utf-8")
    xml = "\n".join([line for line in xml.split("\n") if line.strip()])
    return xml

  def getcontextname(self, contextnode):
    """returns the name of the given context"""
    namenode = getFirstElementByTagName(contextnode, "name")
    return getnodetext(namenode)

  def getcontextnode(self, contextname):
    """finds the contextnode with the given name"""
    contextnode = self.knowncontextnodes.get(contextname, None)
    if contextnode is not None:
      return contextnode
    contextnodes = self.document.searchElementsByTagName("context", self.contextancestors)
    for contextnode in contextnodes:
      if self.getcontextname(contextnode) == contextname:
        self.knowncontextnodes[contextname] = contextnode
        return contextnode
    return None

  def getmessagenodes(self, context=None):
    """returns all the messagenodes, limiting to the given context (name or node) if given"""
    if context is None:
      return self.document.searchElementsByTagName("message", self.messageancestors)
    else:
      if isinstance(context, (str, unicode)):
        # look up the context node by name
        context = self.getcontextnode(context)
        if context is None:
          return []
      return context.searchElementsByTagName("message", self.messageancestors)

  def getmessagesource(self, message):
    """returns the message source for a given node"""
    sourcenode = getFirstElementByTagName(message, "source")
    return getnodetext(sourcenode)

  def getmessagetranslation(self, message):
    """returns the message translation for a given node"""
    translationnode = message.getElementsByTagName("translation")
    return getnodetext(translationnode)

  def getmessagetype(self, message):
    """returns the message translation attributes for a given node"""
    translationnode = getFirstElementByTagName(message, "translation")
    return translationnode.getAttribute("type")

  def getmessagecomment(self, message):
    """returns the message comment for a given node"""
    commentnode = getFirstElementByTagName(message, "comment")
    # NOTE: handles only one comment per msgid (OK)
    # and only one-line comments (can be VERY wrong) TODO!!!
    return getnodetext(commentnode)

  def iteritems(self):
    """iterates through (contextname, messages)"""
    for contextnode in self.document.searchElementsByTagName("context", self.contextancestors):
      yield self.getcontextname(contextnode), self.getmessagenodes(contextnode)

  def __del__(self):
    """clean up the document if required"""
    if hasattr(self, "document"):
      self.document.unlink()

