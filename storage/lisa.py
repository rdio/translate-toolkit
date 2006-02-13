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

"""Parent class for LISA standards (TMX, TBX, XLIFF)"""

from translate.storage import base
from xml.dom import minidom

class LISAunit(base.TranslationUnit):
    """A single unit in the file. 
Provisional work is done to make several languages possible."""
    
    #The name of the root element of this unit type:(termEntry, tu, trans-unit)
    rootNode = ""
    #The name of the per language element of this unit type:(termEntry, tu, trans-unit)
    languageNode = ""
    #The name of the innermost element of this unit type:(term, seg)
    textNode = ""
    
    def __init__(self, source, document=None, empty=False):
        """Constructs a unit containing the given source string"""
        if document:
            self.document = document
        else:
            self.document = minidom.Document()
        if empty:
            return
        self.xmlelement = self.document.createElement(self.rootNode)
        #add descrip, note, etc.
        
        super(LISAunit, self).__init__(source)

    def __eq__(self, other):
        """Compares two units"""
        languageNodes = self.xmlelement.getElementsByTagName(self.languageNode)
        otherlanguageNodes = other.xmlelement.getElementsByTagName(self.languageNode)
        if len(languageNodes) != len(otherlanguageNodes):
            return False
        for i in range(len(languageNodes)):
            mytext = self.getNodeText(languageNodes[i])
            othertext = other.getNodeText(otherlanguageNodes[i])
            if mytext != othertext:
                #TODO:^ maybe we want to take children and notes into account
                return False
        return True
        
    def setsource(self, source, sourcelang='en'):
        languageNodes = self.xmlelement.getElementsByTagName(self.languageNode)
        sourcelanguageNode = self.createlanguageNode(sourcelang, source)
        if len(languageNodes) > 0:
            self.xmlelement.replaceChild(sourcelanguageNode, languageNodes[0])
        else:
            self.xmlelement.appendChild(sourcelanguageNode)
            
    def getsource(self):
        return self.getNodeText(self.getlanguageNode(lang=None, index=0))
    source = property(getsource, setsource)

    def settarget(self, text, lang='xx', append=False):
        #XXX: we really need the language - can't really be optional
        """Sets the "target" string (second language), or alternatively appends to the list"""
        #Firstly deal with reinitialising to None or setting to identical string
        if self.gettarget() == text:
            return
        languageNodes = self.xmlelement.getElementsByTagName(self.languageNode)
        assert len(languageNodes) > 0
	if text:
            languageNode = self.createlanguageNode(lang, text)
            if append or len(languageNodes) == 1:
                self.xmlelement.appendChild(languageNode)
            else:
                self.xmlelement.insertBefore(languageNode, languageNodes[1])
        if not append and len(languageNodes) > 1:
            self.xmlelement.removeChild(languageNodes[1])

    def gettarget(self, lang=None):
        """retrieves the "target" text (second entry), or the entry in the 
	specified language, if it exists"""
        if lang:
            node = self.getlanguageNode(lang=lang)
        else:
            node = self.getlanguageNode(lang=None, index=1)
        return self.getNodeText(node)
    target = property(gettarget, settarget)
                   
    def createlanguageNode(self, lang, text):
        """Returns a xml Element setup with given parameters to represent a 
	single language entry. Has to be overridden."""
        return None

    def getlanguageNode(self, lang=None, index=None):
        """Retrieves a languageNode either by language or by index"""
        if lang is None and index is None:
            raise KeyError("No criterea for languageNode given")
        languageNodes = self.xmlelement.getElementsByTagName(self.languageNode)
        if lang:
            for set in languageNodes:
                if set.getAttribute("xml:lang") == lang:
                    return set
        else:#have to use index
            if index >= len(languageNodes):
                return None
            else:
                return languageNodes[index]
	return None
            
    def getNodeText(self, languageNode):
        """Retrieves the term from the given languageNode"""
        if languageNode is None:
            return None
        terms = languageNode.getElementsByTagName(self.textNode)
        if len(terms) == 0:
            return None
        return self.getText([terms[0]])

    def getText(self, nodelist):
        """joins together the text from all the text nodes in the nodelist and their children"""
        rc = []
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                rc.append(node.data)
            elif node.nodeType == node.ELEMENT_NODE:
                rc += self.getText(node.childNodes)
        return ''.join(rc)
        #return "".join([t.data for t in node.childNodes if t.nodeType == t.TEXT_NODE])

    def __str__(self):
        return self.xmlelement.toxml()

    def createfromxmlElement(cls, element, document):
        term = cls(None, document=document, empty=True)
        term.xmlelement = element
        return term
    createfromxmlElement = classmethod(createfromxmlElement)

class LISAfile(base.TranslationStore):
    """A class representing a file store for one of the LISA file formats."""
    UnitClass = LISAunit
    #The root node of the XML document:
    rootNode = ""
    #The root node of the content section:
    bodyNode = ""
    #The XML skeleton to use for empty construction:
    XMLskeleton = ""

    def __init__(self, inputfile=None, sourcelanguage='en'):
        super(LISAfile, self).__init__()
	self.setsourcelanguage(sourcelanguage)
        if inputfile is not None:
            self.parse(open(inputfile).read())
            assert self.document.documentElement.tagName == self.rootNode
        else:        
            self.parse(self.XMLskeleton)
            self.addheader()

    def addheader(self):
        """Method to be overridden to initialise headers, etc."""
        pass

    def initbody(self):
        """Initialises self.body so it never needs to be retrieved from the DOM again."""
	self.body = self.document.getElementsByTagName(self.bodyNode)[0]

    def setsourcelanguage(self, sourcelanguage):
	"""Sets the source language for this store"""
	self.sourcelanguage = sourcelanguage

    def addsourceunit(self, source):
        #TODO: miskien moet hierdie eerder addsourcestring of iets genoem word?
        """Adds and returns a new unit with the given string as first entry."""
        newunit = self.UnitClass(source, self.document)
        self.addunit(newunit)
        return newunit

    def addunit(self, unit):
        self.body.appendChild(unit.xmlelement)
        self.units.append(unit)

    def __str__(self):
        """Converts to a string containing the file's XML"""
        return self.document.toxml(encoding="utf-8")

    def parse(self, xml):
        """Populates this object from the given xml string"""
        self.document = minidom.parseString(xml)
        assert self.document.documentElement.tagName == self.rootNode
        self.initbody()	   
        termEntries = self.document.getElementsByTagName(self.UnitClass.rootNode)
        if termEntries is None:
            return
        for entry in termEntries:
            term = self.UnitClass.createfromxmlElement(entry, self.document)
            self.units.append(term)

    def parsestring(cls, storestring):
        """Parses the string to return the correct file object"""
        newstore = cls()
        newstore.parse(storestring)
        return newstore
    parsestring = classmethod(parsestring)

    def __del__(self):
        """clean up the document if required"""
        if hasattr(self, "document"):
            self.document.unlink()


