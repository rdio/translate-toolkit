#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2006 Zuza Software Foundation
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

"""module for handling TBX glossary files"""

from translate.storage import base
from xml.dom import minidom

def getnodetext(node):
    #TODO:we probably want this accessible to more modules
    return "".join([t.data for t in node.childNodes if t.nodeType == t.TEXT_NODE])

class tbxunit(base.TranslationUnit):
    """A single term in the TBX file. 
Provisional work is done to make several languages possible."""
    
    def __init__(self, source, document=None, empty=False):
        """Constructs a term containing the given source string"""
        if document:
            self.document = document
        else:
            self.document = minidom.Document()
        if empty:
            return
        self.xmlelement = minidom.Element("termEntry")
        #add descrip, note, etc.
        
        #super(tbxunit, self).__init__(source)
        #TODO^
        self.setsource(source)

    def __eq__(self, other):
        """Compares two terms"""
        langSets = self.xmlelement.getElementsByTagName("langSet")
        otherlangSets = other.xmlelement.getElementsByTagName("langSet")
        if len(langSets) != len(otherlangSets):
            return False
        for i in range(len(langSets)):
            mytext = self.gettermtext(langSets[i])
            othertext = other.gettermtext(otherlangSets[i])
            if mytext != othertext:
                #TODO:^ maybe we want to take children and notes into account
                return False
        return True
        
    def setsource(self, source, sourcelang='en'):
        langSets = self.xmlelement.getElementsByTagName("langSet")
        sourcelangset = self.createlangset(sourcelang, source)
        if len(langSets) > 0:
            self.xmlelement.insertBefore(sourcelangset, langSets[0])
            self.xmlelement.removeChild(langSets[0])
        else:
            self.xmlelement.appendChild(sourcelangset)
            
    def getsource(self):
        return self.gettermtext(self.getlangset(lang=None, index=0))
    source = property(getsource, setsource)

    def settarget(self, text, lang='xx', append=False):
        #XXX: we really need the language - can't really be optional
        """Sets the "target" string (second language), or alternatively appends to the list"""
        langSets = self.xmlelement.getElementsByTagName("langSet")
        assert len(langSets) > 0
        langset = self.createlangset(lang, text)
        if append or len(langSets) == 1:
            self.xmlelement.appendChild(langset)
        else:
            self.xmlelement.insertBefore(langset, langSets[1])
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
        langset.setAttribute("xml:lang", lang)
        tig = self.document.createElement("tig") # or ntig with termGrp inside
        term = self.document.createElement("term")
        termtext = self.document.createTextNode(text)
        term.appendChild(termtext)
        tig.appendChild(term)
        langset.appendChild(tig)
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

    def createfromxmlElement(cls, element):
        term = tbxunit(None, document=None, empty=True)
        term.xmlelement = element
        return term
    createfromxmlElement = classmethod(createfromxmlElement)


class tbxfile(base.TranslationStore):
    """file Base class for stores for multiple translation units of type UnitClass"""
    UnitClass = tbxunit

    def __init__(self, inputfile=None, lang='en'):
        super(tbxfile, self).__init__()
        if inputfile is not None:
            self.document = minidom.parse(inputfile)
            assert self.document.documentElement.tagName == "martif"
        else:        
            self.parse('''<?xml version="1.0"?>
<!DOCTYPE martif PUBLIC "ISO 12200:1999A//DTD MARTIF core (DXFcdV04)//EN" "TBXcdv04.dtd">
<martif type="TBX" xml:lang="''' + lang + '''">
<martifHeader>
 <fileDesc>
  <sourceDesc><p>Translate Toolkit - csv2tbx</p></sourceDesc>
 </fileDesc>
</martifHeader>
<text><body></body></text>
</martif>''')

    def addsourceunit(self, source):
        #TODO: miskien moet hierdie eerder addsourcestring of iets genoem word?
        """Adds and returns a new term with the given string as first entry."""
        newterm = super(tbxfile, self).addsourceunit(source)
        self.document.getElementsByTagName("body")[0].appendChild(newterm.xmlelement)
        return newterm

    def addunit(self, unit):
        self.document.getElementsByTagName("body")[0].appendChild(unit.xmlelement)
        self.units.append(unit)

    def __str__(self):
        """Converts to a string containing the file's XML"""
        return self.document.toxml(encoding="utf-8")

    def parse(self, xml):
        """Populates this object from the given xml string"""
        self.document = minidom.parseString(xml)
        assert self.document.documentElement.tagName == "martif"
        termEntries = self.document.getElementsByTagName("termEntry")
        if termEntries is None:
            return
        for entry in termEntries:
            term = tbxunit.createfromxmlElement(entry)
            self.units.append(term)
            assert len(self.units) > 0

    def parsestring(cls, storestring):
        """Parses the string to return a tbxfile object"""
        newTBX = tbxfile()
        newTBX.parse(storestring)
        return newTBX
    parsestring = classmethod(parsestring)

