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

from translate.storage import base
from xml.dom import minidom
from translate import __version__

# TODO: handle comments
# TODO: handle translation types

class tmxunit(base.TranslationUnit):
  def __init__(self, source, document=None, empty=False):
    """Constructs a unit containing the given source string"""
    if document:
        self.document = document
    else:
        self.document = minidom.Document()
    if empty:
        return
    self.xmlelement = document.createElement("tu")
    #add descrip, note, etc.

    super(tbxunit, self).__init__(source)

  def setsource(self, source, sourcelang='en'):
    langSets = self.xmlelement.getElementsByTagName("langSet")
    sourcelangset = self.createlangset(sourcelang, source)
    if len(langSets) > 0:
      self.xmlelement.replaceChild(sourcelangset, langSets[0])
    else:
      self.xmlelement.appendChild(sourcelangset)
            
  def getsource(self):
    return self.gettermtext(self.getlangset(lang=None, index=0))
  source = property(getsource, setsource)

    def settarget(self, text, lang='xx', append=False):
        #XXX: we really need the language - can't really be optional
        """Sets the "target" string (second language), or alternatively appends to the list"""
        #Firstly deal with reinitialising to None or setting to identical string
        if self.gettarget() == text:
            return
        langSets = self.xmlelement.getElementsByTagName("langSet")
        assert len(langSets) > 0
	if text:
            langset = self.createlangset(lang, text)
            if append or len(langSets) == 1:
                self.xmlelement.appendChild(langset)
            else:
                self.xmlelement.insertBefore(langset, langSets[1])
        if not append and len(langSets) > 1:
            self.xmlelement.removeChild(langSets[1])

    def gettarget(self, lang=None):
        """retrieves the "target" text (second entry), or the entry in the specified language, if it exists"""
        if lang:
            node = self.getlangset(lang=lang)
        else:
            node = self.getlangset(lang=None, index=1)
        return self.gettermtext(node)
    target = property(gettarget, settarget)
                   
    def createlangset(self, lang, text):
        """returns a langset xml Element setup with given parameters"""
        langset = self.document.createElement("langSet")
	assert self.document == langset.ownerDocument
        langset.setAttribute("xml:lang", lang)
        tig = self.document.createElement("tig") # or ntig with termGrp inside
        term = self.document.createElement("term")
        termtext = self.document.createTextNode(text)
        
        langset.appendChild(tig)
        tig.appendChild(term)
        term.appendChild(termtext)
        return langset

    def getlangset(self, lang=None, index=None):
        """Retrieves a langSet either by language or by index"""
        if lang is None and index is None:
            raise KeyError("No criterea for langSet given")
        langsets = self.xmlelement.getElementsByTagName("langSet")
        if lang:
            for set in langsets:
                if set.getAttribute("xml:lang") == lang:
                    return set
        else:#have to use index
            if index >= len(langsets):
                return None
            else:
                return langsets[index]
        raise KeyError("No such langSet found")
            
    def gettermtext(self, langset):
        """Retrieves the term from the given langset"""
        if langset is None:
            return None
        terms = langset.getElementsByTagName("term")
        if len(terms) == 0:
            return None
        return getnodetext(terms[0])
        
    def __str__(self):
        return self.xmlelement.toxml()

    def createfromxmlElement(cls, element, document):
        term = tbxunit(None, document=document, empty=True)
        term.xmlelement = element
        return term
    createfromxmlElement = classmethod(createfromxmlElement)




class TmxParser(base.TranslationStore):
  UnitClass = tmxunit
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

