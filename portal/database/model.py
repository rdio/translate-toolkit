#!/usr/bin/python
#
# Copyright 2004 Thomas Fogwill (tfogwill@users.sourceforge.net)
#
# This file is part of the translate web portal.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA	02111-1307	USA

"""classes that model database elements of the translate portal database. The
attributes of these objects must only be changed using the setX mutators, else
tracking whether the objects need to be saved will fail."""

from translate.portal.database import dbhelper
import pg
from translate.portal.util import Logging
from translate.filters.decoration import *
from translate.filters.prefilters import *

pool=dbhelper.ConnectionPool.getInstance()

       
###############################################################################
# The base class of all persistent objects
###############################################################################
class Persistent:
    """Base class for peristent objects. Subclasses are expected
    to implement the method saveObject
    """
    def __init__(self,id=-1):
        self.changed = 0
        self.id = id
    
    def isNew(self):
        return self.id < 0
    
    def isChanged(self):
        return self.isNew() or self.changed
        
    def save(self):
        try:
            db = pool.getConnection() 
            #call private __saveobject method
            #ugly, but Python doesn't do protected methods, and I don't want 
            #this one to be public
            func = getattr(self, "_" + str(self.__class__).split(".")[-1] + '__saveObject')
            func(db)
            self.changed = 0
            self.new = 0
        except pg.error,e:
            Logging.error(e)
            raise
        else:
            if db: pool.releaseConnection(db)
            
    def __cmp__(self,obj):
        if obj == None: 
            if self: return 99
            else: return 0
        if (self.__class__ == obj.__class__):
            return self.id - obj.id
        else: return 99
            
    def __saveObject(self, db):
        raise NotImplementedError('Method __saveObject not implemented')
 

###############################################################################
# Class to represent data in rows of the file table
###############################################################################
class Project(Persistent):
    
    TABLE = "project"
    ID_COL = "proj_id"
    NAME_COL = "proj_name"
    VERSION_COL = "proj_version"
    ACCEL_INDICATOR_COL = "proj_accelerator_indicator"
        
    def __init__(self,values={}):
        Persistent.__init__(self,values.get(Project.ID_COL, -1))
        self.name = values.get(Project.NAME_COL)
        self.version = values.get(Project.VERSION_COL)
        self.accelerator_indicator = values.get(Project.ACCEL_INDICATOR_COL,'')
        self.__files = None
    
    def setName(self, name):
        self.changed = (self.name != name)
        self.name = name
    
    def setVersion(self, version):
        self.changed = (self.version != version)
        self.version = version
    
    def setAcceleratorIndicator(self, accel_ind):
        self.changed = (self.accelerator_indicator != accel_ind)
        self.accelerator_indicator = accel_ind
            
    def __saveObject(self, db):
        if not self.isChanged():
            return       
        if (self.isNew()): 
            id = db.insert(Project.TABLE, {
                Project.NAME_COL:self.name,
                Project.VERSION_COL:self.version,
                Project.ACCEL_INDICATOR_COL:self.accelerator_indicator
            })
            self.id = id[Project.ID_COL]
        else:
            id = db.update(Project.TABLE, {
                Project.ID_COL:self.id,
                Project.NAME_COL:self.name,
                Project.VERSION_COL:self.version,
                Project.ACCEL_INDICATOR_COL:self.accelerator_indicator
            })           
    
    def getFiles(self):
        if self.__files == None:
            self.__loadFiles()
        return self.__files 
    
    def __loadFiles(self):
        try:
            result = dbhelper.executeQuery("SELECT * FROM %s WHERE %s = %d" % (File.TABLE, File.PROJECT_ID_COL,self.id))
            def setProject(dict):
                dict[File.PROJECT_OBJ_KEY] = self
                return File(dict)
            self.__files = map(setProject,result)
        except pg.error,e:
            Logging.error(e)
            raise
        
    
    def __str__(self):
        return "PROJECT\n====\n   ID: %d\n   NEW: %d\n   CHANGED: %d\n   NAME: %s\n   VERSION: %s\nACCEL_IND:   %s" % (self.id,self.isNew(), \
            self.isChanged(),self.name,self.version,self.accelerator_indicator)

 
       
###############################################################################
# Class to represent data in rows of the file table
###############################################################################
class File(Persistent):
    
    TABLE = "file"
    ID_COL = "file_id"
    NAME_COL = "file_name"
    PROJECT_ID_COL = "proj_id"
    PROJECT_OBJ_KEY = "proj_obj"
        
    def __init__(self,values={}):
        Persistent.__init__(self,values.get(File.ID_COL, -1))
        self.name = values.get(File.NAME_COL)
        self.project = values.get(File.PROJECT_OBJ_KEY)
        if self.project == None:
            self.project = dbhelper.fetchByPK(Project,values.get(File.PROJECT_ID_COL))
        self.__updateAcceleratorIndicator()
        self.__originals = None
    
    def setName(self, name):
        self.changed = (self.name != name)
        self.name = name
        
    def __updateAcceleratorIndicator(self):
        if self.project:
            self.accelerator_indicator = self.project.accelerator_indicator
        
    def setProject(self,project):
        if self.project == None:
            self.changed = (project != None)
        else:
            self.changed = (self.project.id != project.id)
        self.project = project
        self.__updateAcceleratorIndicator()
    
    def __saveObject(self, db):
        if not self.isChanged():
            return       
        if (self.isNew()): 
            id = db.insert(File.TABLE, {
                File.NAME_COL:self.name,
                File.PROJECT_ID_COL:self.project.id
            })
            self.id = id[File.ID_COL]
        else:
            id = db.update(File.TABLE, {
                File.ID_COL:self.id,
                File.NAME_COL:self.name,
                File.PROJECT_ID_COL:self.project.id
            })           
    
    def getOriginals(self):
        if self.__originals == None:
            self.__loadOriginals()
        return self.__originals 
    
    def __loadOriginals(self):
        try:
            result = dbhelper.executeQuery("SELECT * FROM %s WHERE %s = %d" % (Original.TABLE, Original.FILE_ID_COL,self.id))
            def setFile(dict):
                dict[Original.FILE_OBJ_KEY] = self
                return Original(dict)
            self.__originals = map(setFile,result)
        except pg.error,e:
            Logging.error(e)
            raise
        
    
    def __str__(self):
        return "FILE\n====\n   ID: %d\n   NEW: %d\n   CHANGED: %d\n   NAME: %s\nACCEL_IND:   %s" % (self.id,self.isNew(), \
            self.isChanged(),self.name,self.accelerator_indicator)
 
 
       
###############################################################################
# Class to represent data in rows of the language table
###############################################################################
class Language(Persistent):
    
    TABLE = "language"
    ID_COL = "lang_id"
    NAME_COL = "lang_name"
    ISO639_2_COL = "lang_iso639_2"
    ISO639_3_COL = "lang_iso639_3"
    COUNTRY_ISO3166_2_COL = "country_iso3166_2"    
    
    def __init__(self,values={}):
        Persistent.__init__(self,values.get(Language.ID_COL, -1))
        self.name = values.get(Language.NAME_COL)
        self.iso639_2 = values.get(Language.ISO639_2_COL)
        self.iso639_3 = values.get(Language.ISO639_3_COL)
        self.country_iso3166_2 = values.get(Language.COUNTRY_ISO3166_2_COL)
        self.__translations = None
    
    def setName(self,name):
        self.changed = (self.name != name)
        self.name = name
    
    def setISO639_2(self,iso639_2):
        self.changed = (self.iso639_2 != iso639_2)
        self.iso639_2 = iso639_2
    
    def setISO639_3(self,iso639_3):
        self.changed = (self.iso639_3 != iso639_3)
        self.iso639_3 = iso639_3
    
    def setCountryCode(self, country_iso3166_2):
        self.changed = (self.country_iso3166_2 != country_iso3166_2)
        self.country_iso3166_2 = country_iso3166_2
    
    def __saveObject(self, db):
        if not self.isChanged():
            return      
        if (self.isNew()): 
            id = db.insert(Language.TABLE, {
                Language.NAME_COL:self.name,
                Language.ISO639_2_COL:self.iso639_2,
                Language.ISO639_3_COL:self.iso639_3,
                Language.COUNTRY_ISO3166_2_COL:self.country_iso3166_2
            })
            self.id = id[Language.ID_COL]
        else:
            id = db.update(Language.TABLE, {
                Language.ID_COL:self.id,
                Language.NAME_COL:self.name,
                Language.ISO639_2_COL:self.iso639_2,
                Language.ISO639_3_COL:self.iso639_3,
                Language.COUNTRY_ISO3166_2_COL:self.country_iso3166_2
            })         
    
    def getTranslatedStrings(self):
        if self.__translations == None:
            self.__loadTranslations()
        return self.__translations
    
    def __loadTranslations(self):
        try:
            result = dbhelper.executeQuery("SELECT * FROM %s WHERE %s = %d" % (Translation.TABLE, Translation.LANGUAGE_ID_COL,self.id))
            def setLanguage(dict):
                dict[Translation.LANGUAGE_OBJ_KEY] = self
                return Translation(dict)
            self.__translations = map(setLanguage,result)
        except pg.error,e:
            Logging.error(e)
            raise
        
    
    def __str__(self):
        s = []
        s.append("LANGUAGE")
        s.append("========")
        s.append("   ID: %d")
        s.append("   NEW: %d")
        s.append("   CHANGED: %d")
        s.append("   NAME: %s")
        s.append("   ISO2: %s")
        s.append("   ISO3: %s")
        s.append("   COUNTRY: %s")
        return "\n".join(s) % (self.id,self.isNew(), \
            self.isChanged(),self.name,self.iso639_2,
            self.iso639_3, self.country_iso3166_2)
 
 
       
###############################################################################
# Base class for classes representing data in rows of the original and 
# translation tables
###############################################################################
class POString(Persistent):
    def __init__(self,id=-1,raw='',accel_ind=''):
        Persistent.__init__(self,id)
        self.raw = raw
        self.accelerator_indicator = accel_ind
        
    def setRaw(self, raw):
        self.changed = (self.raw != raw)
        self.raw = raw
        
    def getAccelerator(self):   
        if self.accelerator_indicator == None \
            or self.accelerator_indicator == '' \
            or self.accelerator_indicator == ' '\
            or self.raw == ''\
            or self.raw == None:
            return ''  
        accels = findaccelerators(self.raw,self.accelerator_indicator)
        if accels:
            return accels[0][1]        
        return ''
    
    def getStripped(self):  
        if self.accelerator_indicator == None \
            or self.accelerator_indicator == '' \
            or self.accelerator_indicator == ' '\
            or self.raw == ''\
            or self.raw == None:
            return self.raw
        return filteraccelerators(self.accelerator_indicator)(self.raw)
    
    def getWordcount(self):
        if self.raw == None:
            tmp = ''
        else:
            tmp = self.raw
        s = tmp.replace(',', ' ').replace('.', ' ')
        s = s.replace(';', ' ').replace(':',' ').replace('!', ' ')
        s = s.replace('(',' ').replace(')',' ').replace('?',' ')
        return len(s.split())
    
    def getCharcount(self):
        if self.raw == None:
            tmp = ''
        else:
            tmp = self.raw
        return len(tmp)
 
 
       
###############################################################################
# Class to represent data in rows of the original table
###############################################################################
class Original(Persistent, POString):
    
    TABLE = "original"
    ID_COL = "orig_id"
    LOCATION_COL = "orig_location"
    TRANSLATOR_COMMENT_COL = "orig_translator_comment"
    COMMENT_COL = "orig_comment"
    FILE_ID_COL = "file_id"
    RAW_COL = "orig_string_raw"
    STRIPPED_COL = "orig_string_stripped"
    WORDCOUNT_COL = "orig_wordcount"
    CHARCOUNT_COL = "orig_charcount"
    ACCELERATOR_COL = "orig_accelerator"
    DATE_FIRST_COL = "orig_date_first"
    FILE_OBJ_KEY = "file_obj"
    
    def __init__(self,values={}):
        POString.__init__(self,values.get(Original.ID_COL, -1),values.get(Original.RAW_COL))
        self.location = values.get(Original.LOCATION_COL)
        self.translator_comment = values.get(Original.TRANSLATOR_COMMENT_COL)
        self.comment = values.get(Original.COMMENT_COL)        
        self.file = values.get(Original.FILE_OBJ_KEY)
        if self.file == None:
            self.file = dbhelper.fetchByPK(File,values.get(Original.FILE_ID_COL))
        self.datefirst = values.get(Original.DATE_FIRST_COL)
        self.__translations = None
        self.__updateAcceleratorIndicator()
        
    def __updateAcceleratorIndicator(self):
        if self.file:
            self.accelerator_indicator = self.file.accelerator_indicator
        
    def setLocation(self,location):
        self.changed = (self.location != location)
        self.location = location
        
    def setTranslatorComment(self,translator_comment):
        self.changed = (self.translator_comment != translator_comment)
        self.translator_comment = translator_comment
        
    def setComment(self,comment):
        self.changed = (self.comment != comment)
        self.location = comment
        
    def setFile(self,file):
        if self.file == None:
            self.changed = (file != None)
        else:
            self.changed = (self.file.id != file.id)
        self.file = file
        self.__updateAcceleratorIndicator()
        
    def setDatefirst(self,date):
        self.changed = (self.datefirst != date)
        self.datefirst = date
        
    def __saveObject(self, db):
        if not self.isChanged():
            return
        if self.file.isChanged(): self.file.save()      
        if (self.isNew()): 
            id = db.insert(Original.TABLE, {
                Original.LOCATION_COL:self.location,
                Original.TRANSLATOR_COMMENT_COL:self.translator_comment,
                Original.RAW_COL:self.raw,
                Original.COMMENT_COL:self.comment,
                Original.ACCELERATOR_COL:self.getAccelerator(),
                Original.STRIPPED_COL:self.getStripped(),
                Original.WORDCOUNT_COL:self.getWordcount(),
                Original.CHARCOUNT_COL:self.getCharcount(),
                Original.FILE_ID_COL:self.file.id              
            })
            self.id = id[Original.ID_COL]
        else:
            id = db.update(Original.TABLE, {
                Original.ID_COL:self.id,
                Original.LOCATION_COL:self.location,
                Original.TRANSLATOR_COMMENT_COL:self.translator_comment,
                Original.RAW_COL:self.raw,
                Original.COMMENT_COL:self.comment,
                Original.ACCELERATOR_COL:self.getAccelerator(),
                Original.STRIPPED_COL:self.getStripped(),
                Original.WORDCOUNT_COL:self.getWordcount(),
                Original.CHARCOUNT_COL:self.getCharcount(),
                Original.FILE_ID_COL:self.file.id              
            })        
    
    def getTranslations(self):
        if self.__translations == None:
            self.__loadTranslations()
        return self.__translations
    
    def __loadTranslations(self):
        try:
            result = dbhelper.executeQuery("SELECT * FROM %s WHERE %s = %d" % (Translation.TABLE, Translation.ORIGINAL_ID_COL,self.id))
            def setOriginal(dict):
                dict[Translation.ORIGINAL_OBJ_KEY] = self
                return Translation(dict)
            self.__translations = map(setOriginal,result)
        except pg.error,e:
            Logging.error(e)
            raise
        
        
    def __str__(self):
        s = []
        s.append("ORIGINAL")
        s.append("========")
        s.append("   ID: %d")
        s.append("   NEW: %d")
        s.append("   CHANGED: %d")
        s.append("   LOCATION: %s")
        s.append("   TRANS_COMMENT: %s")
        s.append("   RAW: %s")
        s.append("   COMMENT: %s")
        s.append("   ACCEL: %s")
        s.append("   STRIPPED: %s")
        s.append("   WORDS: %d")
        s.append("   CHARS: %d")
        s.append("   FILE_ID: %d")
        return "\n".join(s) % (self.id,self.isNew(),
            self.isChanged(),self.location,self.translator_comment,self.raw, 
            self.comment,self.getAccelerator(),self.getStripped(), 
            self.getWordcount(),self.getCharcount(),self.file.id)
 
 
       
###############################################################################
# Class to represent data in rows of the translation table
###############################################################################
class Translation(POString):
    
    TABLE = "translation"
    ID_COL = "trans_id"
    VERSION_COL = "trans_version"
    RAW_COL = "trans_string_raw"
    STRIPPED_COL = "trans_string_stripped"
    WORDCOUNT_COL = "trans_wordcount"
    CHARCOUNT_COL = "trans_charcount"
    ACCELERATOR_COL = "trans_accelerator"
    ORIGINAL_ID_COL = "orig_id"
    LANGUAGE_ID_COL = "lang_id"
    DATE_FIRST_COL = "trans_date_first"
    LANGUAGE_OBJ_KEY = "lang_obj"
    ORIGINAL_OBJ_KEY = "orig_obj"
    
    
    def __init__(self,values={}):
        POString.__init__(self,values.get(Translation.ID_COL, -1),values.get(Translation.RAW_COL))
        self.version = values.get(Translation.VERSION_COL)
        self.datefirst = values.get(Translation.DATE_FIRST_COL)        
        self.original = values.get(Translation.ORIGINAL_OBJ_KEY)
        if self.original == None:
            self.original = dbhelper.fetchByPK(Original, values.get(Translation.ORIGINAL_ID_COL))        
        self.language = values.get(Translation.LANGUAGE_OBJ_KEY)
        if self.language == None:
            self.language = dbhelper.fetchByPK(Language,values.get(Translation.LANGUAGE_ID_COL))
        self.__updateAcceleratorIndicator()
        
    def __updateAcceleratorIndicator(self):
        if self.original:
            self.accelerator_indicator = self.original.accelerator_indicator
        
    def setVersion(self,version):
        self.changed = (self.version != version)
        self.version = version
        
    def setOriginal(self,original):
        if (self.original == None):
            self.changed = (original != None)
        else:
            self.changed = (self.original.id != original.id)
        self.original = original
        self.__updateAcceleratorIndicator()
        
    def setLanguage(self,language):
        if (self.language == None):
            self.changed = (language != None)
        else:
            self.changed = (self.language.id != language.id)
        self.language = language
        
    def setDatefirst(self,date):
        self.changed = (self.datefirst != date)
        self.datefirst = date
        
    def __saveObject(self, db):
        if not self.isChanged():
            return
        if self.original.isChanged(): self.original.save()
        if self.language.isChanged(): self.language.save()   
        if (self.isNew()): 
            id = db.insert(Translation.TABLE, {
                Translation.VERSION_COL:self.version,
                Translation.RAW_COL:self.raw,
                Translation.ACCELERATOR_COL:self.getAccelerator(),
                Translation.STRIPPED_COL:self.getStripped(),
                Translation.WORDCOUNT_COL:self.getWordcount(),
                Translation.CHARCOUNT_COL:self.getCharcount(),
                Translation.ORIGINAL_ID_COL:self.original.id,
                Translation.LANGUAGE_ID_COL:self.language.id
            })
            self.id = id[Translation.ID_COL]
        else:
            id = db.update(Translation.TABLE, {
                Translation.ID_COL:self.id,
                Translation.VERSION_COL:self.version,
                Translation.RAW_COL:self.raw,
                Translation.ACCELERATOR_COL:self.getAccelerator(),
                Translation.STRIPPED_COL:self.getStripped(),
                Translation.WORDCOUNT_COL:self.getWordcount(),
                Translation.CHARCOUNT_COL:self.getCharcount(),
                Translation.ORIGINAL_ID_COL:self.original.id,
                Translation.LANGUAGE_ID_COL:self.language.id
            })
        
    def __str__(self):
        s = []
        s.append("TRANSLATION")
        s.append("========")
        s.append("   ID: %d")
        s.append("   NEW: %d")
        s.append("   CHANGED: %d")
        s.append("   RAW: %s")
        s.append("   VERSION: %s")
        s.append("   ACCEL: %s")
        s.append("   STRIPPED: %s")
        s.append("   WORDS: %d")
        s.append("   CHARS: %d")
        s.append("   ORIG_ID: %d")
        s.append("   LANG_ID: %d")
        return "\n".join(s) % (self.id,self.isNew(),
            self.isChanged(),self.raw,self.version,
            self.getAccelerator(),self.getStripped(), 
            self.getWordcount(),self.getCharcount(),
            self.original.id,self.language.id)
 
 
 
       
###############################################################################
# Main ....
###############################################################################
if __name__ == '__main__':
    project = Project()
    project.setName('Test proj')
    project.setVersion('test version')
    project.setAcceleratorIndicator('_')
    print project
    project.save()
    print project
    file = File()
    file.setName('testing file')
    file.setProject(project)
    print file
    file.save()
    print file
    file.setName('tested file')
    original = Original()
    original.setLocation('location: line 213')
    original.setTranslatorComment('My translator comment')
    original.setComment('My comment')
    original.setRaw('My __little _test &&original &string')
    original.setFile(file)
    original.save()
    print original
    language = Language()
    language.setName("Afrikaans")
    language.setISO639_2("af")
    language.setISO639_3("afr")
    language.setCountryCode("ZA")
    translation = Translation()
    translation.setOriginal(original)
    translation.setLanguage(language)
    translation.setVersion("1.0")
    translation.setRaw("_Vertaalde &weergawe __van &&die string")
    print language
    print translation
    translation.save()
    print language
    print translation
	
###############################################################################
# fin.
###############################################################################
	