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

"""Converts Gettext .po files to .xliff localization files
You can convert back from .xliff to .po using po2xliff"""

from translate.storage import po
from translate.storage import xliff
from translate.misc import quote
from xml.dom import minidom

class PoXliffParser(xliff.XliffParser):
  """a parser for the po variant of Xliff files"""
  def createfilenode(self, filename):
    """creates a filenode with the given filename"""
    filenode = super(PoXliffParser, self).createfilenode(filename)
    filenode.setAttribute("datatype", "po")
    filenode.setAttribute("source-language", "en-US")
    return filenode

  def addtransunit(self, filename, transunitnode, createifmissing=False):
    """adds the given trans-unit (will create the nodes required if asked). Returns success"""
    filenode = self.getfilenode(filename)
    if filenode is None:
      if not createifmissing:
        return False
      filenode = self.createfilenode(filename)
      self.document.documentElement.appendChild(filenode)
    for transunit in self.gettransunitnodes(filenode):
      pass
    if not createifmissing:
      return False
    bodynode = self.getbodynode(filenode, createifmissing=createifmissing)
    if bodynode is None: return False
    bodynode.appendChild(transunitnode)
    transunitnode.ownerDocument = self.document
    messagenum = len(bodynode.getElementsByTagName("trans-unit"))
    transunitnode.setAttribute("id", "messages_%d" % messagenum)
    return True

  def getheadernode(self, filenode, createifmissing=False):
    """finds the header node for the given filenode"""
    headernodes = filenode.getElementsByTagName("header")
    if headernodes:
      return headernodes[0]
    if not createifmissing:
      return None
    headernode = minidom.Element("header")
    filenode.appendChild(headernode)
    return headernode

  def getbodynode(self, filenode, createifmissing=False):
    """finds the body node for the given filenode"""
    bodynodes = filenode.getElementsByTagName("body")
    if bodynodes:
      return bodynodes[0]
    if not createifmissing:
      return None
    bodynode = self.document.createElement("body")
    filenode.appendChild(bodynode)
    return bodynode

class po2xliff:
  def createtransunit(self, thepo):
    """creates a transunit node"""
    source = po.unquotefrompo(thepo.msgid, joinwithlinebreak=False).replace("\\n", "\n")
    translation = po.unquotefrompo(thepo.msgstr, joinwithlinebreak=False).replace("\\n", "\n")
    if isinstance(source, str):
      source = source.decode("utf-8")
    if isinstance(translation, str):
      translation = translation.decode("utf-8")
    transunitnode = minidom.Element("trans-unit")
    sourcenode = minidom.Element("source")
    sourcetext = minidom.Text()
    sourcetext.data = source
    sourcenode.appendChild(sourcetext)
    transunitnode.appendChild(sourcenode)
    targetnode = minidom.Element("target")
    targettext = minidom.Text()
    targettext.data = translation
    targetnode.appendChild(targettext)
    transunitnode.appendChild(targetnode)
    for sourcelocation in thepo.getsources():
      transunitnode.appendChild(self.createcontextgroup(sourcelocation))
    return transunitnode

  def maketextnode(self, text):
    textnode = minidom.Text()
    textnode.data = text
    return textnode

  def createcontextgroup(self, sourcelocation):
    """creates an xliff context group for the given po sourcelocation"""
    if ":" in sourcelocation:
      sourcefile, linenumber = sourcelocation.split(":", 1)
    else:
      sourcefile, linenumber = sourcelocation, None
    sourcefilenode = minidom.Element("context")
    sourcefilenode.setAttribute("context-type", "sourcefile")
    sourcefilenode.appendChild(self.maketextnode(sourcefile))
    contextgroupnode = minidom.Element("context-group")
    contextgroupnode.setAttribute("name", "x-po-reference")
    contextgroupnode.setAttribute("purpose", "location")
    contextgroupnode.appendChild(sourcefilenode)
    if linenumber is not None:
      linenumbernode = minidom.Element("context")
      linenumbernode.setAttribute("context-type", "linenumber")
      linenumbernode.appendChild(self.maketextnode(linenumber))
      contextgroupnode.appendChild(linenumbernode)
    return contextgroupnode

  def convertfile(self, inputfile, templatefile):
    """converts a .po file to .xliff format"""
    if templatefile is None: 
      xlifffile = PoXliffParser()
    else:
      xlifffile = PoXliffParser(templatefile)
    thepofile = po.pofile(inputfile)
    filename = thepofile.filename
    for thepo in thepofile.poelements:
      if thepo.isblank():
        continue
      transunitnode = self.createtransunit(thepo)
      xlifffile.addtransunit(filename, transunitnode, True)
    return xlifffile.getxml()

def convertpo(inputfile, outputfile, templatefile):
  """reads in stdin using fromfileclass, converts using convertorclass, writes to stdout"""
  convertor = po2xliff()
  outputxliff = convertor.convertfile(inputfile, templatefile)
  outputfile.write(outputxliff)
  return 1

def main():
  from translate.convert import convert
  formats = {"po": ("xliff", convertpo), ("po", "xliff"): ("xliff", convertpo)}
  parser = convert.ConvertOptionParser(formats, usepots=True, usetemplates=True, description=__doc__)
  parser.run()

