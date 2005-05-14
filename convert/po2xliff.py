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
  def __init__(self,*args,**kwargs):
    xliff.XliffParser.__init__(self,*args,**kwargs)
    self._filename = None
    
  def createfilenode(self, filename):
    """creates a filenode with the given filename"""
    filenode = super(PoXliffParser, self).createfilenode(filename)
    filenode.setAttribute("datatype", "po")
    filenode.setAttribute("source-language", "en-US")
    return filenode


  def addtransunit(self, filename, transunitnode, createifmissing=False):
    """adds the given trans-unit to the last used body node if the filename has changed it uses the slow method instead (will create the nodes required if asked). Returns success"""
    if self._filename != filename:
      return self.slow_addtransunit(filename, transunitnode, createifmissing)
    self._bodynode.appendChild(transunitnode)
    transunitnode.ownerDocument = self.document
    self._messagenum += 1
    transunitnode.setAttribute("id", "messages_%d" % self._messagenum)
    return True

  def slow_addtransunit(self, filename, transunitnode, createifmissing=False):
    """adds the given trans-unit (will create the nodes required if asked). Returns success"""
    self._filename = filename
    
    filenode = self.getfilenode(filename)
    if filenode is None:
      if not createifmissing:
        return False
      filenode = self.createfilenode(filename)
      self.document.documentElement.appendChild(filenode)

    
    if not createifmissing:
      return False
    bodynode = self.getbodynode(filenode, createifmissing=createifmissing)
    self._bodynode = bodynode
    if bodynode is None: return False
    bodynode.appendChild(transunitnode)
    transunitnode.ownerDocument = self.document
    messagenum = len(bodynode.getElementsByTagName("trans-unit"))

    self._messagenum = messagenum

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

#------------

def _findAllMatches(text,re_obj):
  'generate match objects for all @re_obj matches in @text'
  start = 0
  max = len(text)
  while start < max:
    m = re_obj.search(text, start)
    if not m: break
    yield m
    start = m.end()

import re
placeholders = ['(%[diouxXeEfFgGcrs])',r'(\\+.?)','(%[0-9]$lx)','(%[0-9]\$[a-z])','(<.+?>)']
re_placeholders = [re.compile(ph) for ph in placeholders]
def _getPhMatches(text):
  'return list of regexp matchobjects for with all place holders in the @text'
  matches = []
  for re_ph in re_placeholders:
    matches.extend(list(_findAllMatches(text,re_ph)))

  # sort them so they come sequentially
  matches.sort(lambda a,b: cmp(a.start(),b.start()))
  return matches

  
#------------


class po2xliff:
  def createtransunit(self, thepo):
    """creates a transunit node"""
    if not thepo.hasplural():
      source = po.unquotefrompo(thepo.msgid, joinwithlinebreak=False).replace("\\n", "\n")
      translation = po.unquotefrompo(thepo.msgstr, joinwithlinebreak=False).replace("\\n", "\n")
      if isinstance(source, str):
        source = source.decode("utf-8")
      if isinstance(translation, str):
        translation = translation.decode("utf-8")
      transunitnode = minidom.Element("trans-unit")
      sourcenode = self.createXliffNode("source",source)
      transunitnode.appendChild(sourcenode)
      if translation:
        targetnode = self.createXliffNode("target",translation)
        transunitnode.appendChild(targetnode)
        if thepo.isfuzzy():
          targetnode.setAttribute("state", "needs-review-translation")
          targetnode.setAttribute("state-qualifier", "fuzzy-match")
        else:
          targetnode.setAttribute("state", "translated")
      for sourcelocation in thepo.getsources():
        transunitnode.appendChild(self.createcontextgroup(sourcelocation))
      return transunitnode
    else:
      print "po2xliff does not currently handle plural messages"
      return None
        

  def maketextnode(self, text):
    textnode = minidom.Text()
    textnode.data = text
    return textnode

  def createXliffNode(self,nodename,text):
    '''
    Create a Xliff Source/Target node with placeholder tags
    @nodename: 'target' or 'source'
    @text: text to add to node
    returns the node created
    '''
    node = minidom.Element(nodename)

    start = 0
    for i,m in enumerate(_getPhMatches(text)):
      #pretext
      node.appendChild(self.maketextnode(text[start:m.start()]))
      #ph node 
      phnode = minidom.Element("ph")
      phnode.setAttribute("id", str(i+1))
      phnode.appendChild(self.maketextnode(m.group()))
      node.appendChild(phnode)
      start = m.end()
    #post text
    node.appendChild(self.maketextnode(text[start:]))
    return node

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

  def convertfile(self, thepofile, templatefile):
    """converts a .po file to .xliff format"""
    if templatefile is None: 
      xlifffile = PoXliffParser()
    else:
      xlifffile = PoXliffParser(templatefile)
    filename = thepofile.filename
    for thepo in thepofile.poelements:
      if thepo.isblank():
        continue
      transunitnode = self.createtransunit(thepo)
      if transunitnode:
        xlifffile.addtransunit(filename, transunitnode, True)
    return xlifffile.getxml(pretty=False)

def convertpo(inputfile, outputfile, templatefile):
  """reads in stdin using fromfileclass, converts using convertorclass, writes to stdout"""
  inputpo = po.pofile(inputfile)
  if inputpo.isempty():
    return 0
  convertor = po2xliff()
  outputxliff = convertor.convertfile(inputpo, templatefile)
  outputfile.write(outputxliff)
  return 1

def main():
  from translate.convert import convert
  formats = {"po": ("xliff", convertpo), ("po", "xliff"): ("xliff", convertpo)}
  parser = convert.ConvertOptionParser(formats, usepots=True, usetemplates=True, description=__doc__)
  parser.run()

