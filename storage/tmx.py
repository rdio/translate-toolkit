#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2002-2006 Zuza Software Foundation
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

"""module for parsing TMX translation memeory files"""

from xml.dom import minidom
from translate import __version__

# TODO: handle comments
# TODO: handle translation types

class TmxParser:
  def __init__(self, inputfile=None, sourcelanguage='en'):
    """make a new TmxParser, reading from the given inputfile if required"""
    self.filename = getattr(inputfile, "filename", None)
    if inputfile is None:
      self.document = minidom.parseString('''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE tmx SYSTEM "tmx14.dtd">
<tmx 
version="1.4"><header></header><body></body></tmx>''')
      self.setsourcelanguage(sourcelanguage)
      # TODO Add header info here
      self.addheader()
    else:
      self.document = minidom.parse(inputfile)
      assert self.document.documentElement.tagName == "tmx"
    self.bodynode = self.document.getElementsByTagName("body")[0]

  def addheader(self):
    headernode = self.document.getElementsByTagName("header")[0]
    headernode.setAttribute("creationtool", "Translate Toolkit - po2tmx")
    headernode.setAttribute("creationtoolversion", __version__.ver)
    headernode.setAttribute("segtype", "sentence")
    headernode.setAttribute("o-tmf", "UTF-8")
    headernode.setAttribute("adminlang", "en")
    #TODO: consider adminlang. Used for notes, etc. Possibly same as targetlanguage
    headernode.setAttribute("srclang", self.sourcelanguage)
    headernode.setAttribute("datatype", "PlainText")
    #headernode.setAttribute("creationdate", "YYYYMMDDTHHMMSSZ"
    #headernode.setAttribute("creationid", "CodeSyntax"

  def setsourcelanguage(self, sourcelanguage):
    self.sourcelanguage = sourcelanguage
    headernode = self.document.getElementsByTagName("header")[0]
    headernode.setAttribute("srclang", self.sourcelanguage)

  def addtranslation(self, source, srclang, translation, translang):
    """adds the given translation (will create the nodes required if asked). Returns success"""
    tunode = self.document.createElement("tu")
    self.bodynode.appendChild(tunode)

    # Source
    tuvnode = self.document.createElement("tuv")
    tuvnode.setAttribute("xml:lang", srclang)
    segnode = self.document.createElement("seg")
    sourcetext = self.document.createTextNode(source)
    segnode.appendChild(sourcetext)
    tunode.appendChild(tuvnode).appendChild(segnode)

    # Translation
    tuvnode = self.document.createElement("tuv")
    tuvnode.setAttribute("xml:lang", translang)
    segnode = self.document.createElement("seg")
    translationtext = self.document.createTextNode(translation)
    segnode.appendChild(translationtext)
    tunode.appendChild(tuvnode).appendChild(segnode)

    return True

  def getnodetext(self, node):
    """returns the node's text by iterating through the child nodes"""
    return "".join([t.data for t in node.childNodes if t.nodeType == t.TEXT_NODE])

  def getxml(self):
    """return the TMX file as xml"""
    #we can't do pretty XML as it inserts wrong newlines inside translations
    return self.document.toxml(encoding="utf-8")

  def getunits(self):
    return self.document.getElementsByTagName("tu")

  def getvariants(self, unit):
    return unit.getElementsByTagName("tuv")

  def getsegmenttext(self, variant):
    #Only one <seg> is allowed per variant
    return self.getnodetext(variant.getElementsByTagName("seg")[0])

  def translate(self, sourcetext, sourcelang=None, targetlang=None):
    """translates sourcetext from this memory"""
    #TODO: consider source and target languages
    found = False
    for unit in self.getunits():
      for variant in self.getvariants(unit):
        if found:
          return self.getsegmenttext(variant)
        if self.getsegmenttext(variant) == sourcetext:
          found = True
    return None

  def __del__(self):
    """clean up the document if required"""
    if hasattr(self, "document"):
      self.document.unlink()

