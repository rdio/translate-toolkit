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

"""module for parsing .xliff files for translation"""

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
        _write_data(writer, attrs[a_name].value)
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

# TODO: handle comments
# TODO: handle translation types

class XliffParser:
  def __init__(self, inputfile=None):
    """make a new XliffParser, reading from the given inputfile if required"""
    self.filename = getattr(inputfile, "filename", None)
    if inputfile is None:
      self.document = minidom.parseString('''<?xml version="1.0" ?><xliff version='1.1' xmlns='urn:oasis:names:tc:xliff:document:1.1' xmlns:po='urn:oasis:names:tc:xliff:document:1.1:po-guide'></xliff>''')
    else:
      self.document = minidom.parse(inputfile)
      assert self.document.documentElement.tagName == "xliff"

  def getnodetext(self, node):
    """returns the node's text by iterating through the child nodes"""
    return "".join([t.data for t in node.childNodes if t.nodeType == t.TEXT_NODE])

  def getxml(self):
    """return the ts file as xml"""
    xml = self.document.toprettyxml(indent="    ", encoding="utf-8")
    xml = "\n".join([line for line in xml.split("\n") if line.strip()])
    return xml

  def getfilename(self, filenode):
    """returns the name of the given file"""
    return filenode.attributes.get("original", None)

  def getfilenode(self, filename):
    """finds the filenode with the given name"""
    filenodes = self.document.getElementsByTagName("file")
    for filenode in filenodes:
      if self.getfilename(filenode) == filename:
        return filenode
    return None

  def gettransunitnodes(self, filenode=None):
    """returns all the transunitnodes, limiting to the given file (name or node) if given"""
    if filenode is None:
      return self.document.getElementsByTagName("trans-unit")
    else:
      if isinstance(filenode, (str, unicode)):
        # look up the file node by name
        filenode = self.getfilenode(filenode)
        if filenode is None:
          return []
      return filenode.getElementsByTagName("trans-unit")

  def gettransunitsource(self, transunit):
    """returns the transunit source for a given node"""
    sourcenode = transunit.getElementsByTagName("source")[0]
    return self.getnodetext(sourcenode)

  def gettransunittarget(self, transunit):
    """returns the transunit target for a given node"""
    translationnode = transunit.getElementsByTagName("target")[0]
    return self.getnodetext(translationnode)

  def iteritems(self):
    """iterates through (file, transunits)"""
    for filenode in self.document.getElementsByTagName("file"):
      yield self.getfilename(filenode), self.gettransunitnodes(filenode)

  def __del__(self):
    """clean up the document if required"""
    if hasattr(self, "document"):
      self.document.unlink()

