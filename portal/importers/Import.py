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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA      02111-1307      USA
                                                                                                                                                                                                     
"""An importer to import files/projects into the portal database.
It should be trivial to create project specific wrapper scripts around this one 
(e.g. that know KDE dir layout, etc. """

import sys
import os
from translate.storage.po import pofile
from translate.portal.database.model import *
from translate.portal.database import dbhelper
from mx.DateTime import DateTime

class Importer:
    "A class to represent a single run through the importing process"
    def __init__(self):
        self.project_name = None
        self.project_version = None
        self.accel = None
        self.__project = None
        self.pot = None
        self.__file = None
        self.language_name = None
        self.__language = None
        self.translated = None
        self.po = None
        
    def setProjectName(self,name):
        "setProjectName(name) -> Set the project name if not already set"
        if self.project_name:
            raise "Project name specified more than once"
        elif len(name) == 0:
            raise "Project name length must be > 0"
        else:
            self.project_name = name
        
    def setProjectVersion(self,version):
        "setProjectVersion(version) -> Set the project version if not already set"
        if self.project_version:
            raise "Project version specified more than once"
        elif len(version) == 0:
            raise "Project version length must be > 0"
        else:
            self.project_version = version
        
    def setAccel(self,accel):
        "setAccel(accel) -> Set the accelerator char if not already set"
        if self.accel:
            raise "Project accelerator specified more than once"
        elif len(accel) != 1:
            raise "Accelerator must be a single character"
        else:
            self.accel = accel
        
    def setTemplate(self,pot):
        "setTemplate(pot) -> Set the template filename if not already set"
        if self.pot:
            raise "Template file specified more than once"
        elif len(pot) == 0:
            raise "Template filename length must be > 0"
        elif not os.path.exists(pot) or not os.path.isfile(pot):
            raise "Template file does not exist"
        else:
            self.pot = pot
        
    def setLanguageName(self,language_name):
        "setLanguageName(language_name) -> Set the language name if not already set"
        if self.language_name:
            raise "Language specified more than once"
        elif len(language_name) == 0:
            raise "Language name length must be > 0"
        else:
            self.language_name = language_name
        
    def setTranslated(self,translated):
        "setTranslated(translated) -> Set the flag to indicate that we're importing translated strings (if not already set)"
        if self.translated != None:
            raise "Translated flag specified more than once"
        else:
            self.translated = translated
        
    def setTranslatedFile(self,po):
        "setTranslatedFile(po) -> Set the po filename if the file exists"
        if not os.path.exists(po) or not os.path.isfile(po):
            raise "Translated PO file does not exist"
        self.po = po
        
    def __doProject(self):
        "__doProject() -> Setup the project to import into; create a new one if required"
        if not self.project_name:
            self.project_name = prompt(msg="Please enter the project name: ",name="Project name",min=1,max=256)
        if not self.project_version:
            self.project_name = prompt(msg="Please enter the project version: ",name="Project version",min=1,max=16)
        records = dbhelper.retrieve(Project, {Project.NAME_COL:self.project_name,Project.VERSION_COL:self.project_version})
        if records:
            self.__project = records[0]
        else:
            create = promptYesNo(msg="Project " + self.project_name + "(" + self.project_version + \
                ") does not exist in the database.\n Do you wish to create it?", default=False)
            if not create:
                exit('Not creating new project.')
            if not self.accel:
                 self.accel = prompt(msg="Please enter the accelerator character for the project: ",name="Accelerator",min=1,max=1)
            self.__project = Project()
            self.__project.setName(self.project_name)
            self.__project.setVersion(self.project_version)
            self.__project.setAcceleratorIndicator(self.accel)
            self.__project.save()
            
    def __cleanupString(self,string):
        "Strip quotes from the start and end of strings"
        if string == None or len(string) == 0: 
            return ''
        tmp = string
        if tmp.endswith('"'):
            tmp = tmp[:-1]
        if tmp.startswith('"'):
            tmp = tmp[1:]
        return tmp
    
    
            
    def __importOriginals(self):
        "__importOriginals() -> Import the original strings from the template file (pot)"
        #del existing translations
        dbhelper.executeCustomDelete("delete from %s where %s in (select %s from %s where %s = %d)" % \
            (Translation.TABLE,Translation.ORIGINAL_ID_COL,Original.ID_COL, \
            Original.TABLE,Original.FILE_ID_COL,self.__file.id))
        #del existing originals
        dbhelper.executeCustomDelete("delete from %s where %s = %d" % \
            (Original.TABLE,Original.FILE_ID_COL,self.__file.id))
        #import new originals        
        file = open(self.pot)
        po = pofile(file)
        file.close()
        for elem in po.poelements:  
            origObj = Original()  
            origObj.setFile(self.__file)
            origObj.setRaw(' '.join([self.__cleanupString(s) for s in elem.msgid]))
            origObj.setComment(' '.join([self.__cleanupString(s) for s in elem.visiblecomments]))
            origObj.setTranslatorComment(' '.join([self.__cleanupString(s) for s in elem.othercomments])) 
            origObj.setLocation(' '.join([self.__cleanupString(s) for s in elem.sourcecomments]))       
            # TODO: calculate these somehow somewhere
            origObj.setDatefirst(DateTime(2004,1,1))
            origObj.save()
           
        
    def __doFile(self):
        "__doFile() -> Setup the template file (pot) to import; create a new one if required"
        if not self.pot:
            self.pot = promptFile(msg="Please enter the name of the template (pot) file: ",name="Template filename",mustExist=True)
        records = dbhelper.retrieve(File, {File.NAME_COL:self.pot,File.PROJECT_ID_COL:self.__project.id})
        importOriginals = False
        if records:
            self.__file = records[0]
            if self.__file.getOriginals():
                if self.translated:
                    print "\nTemplate file exists in database. Assuming everything is fine and proceeding with import of translated strings."
                else:
                    importOriginals = promptYesNo(msg="Template file and original strings already exist in the database.\n"\
                        "Do you wish to recreate them (any existing translations in "\
                        "the database will be lost)?", default=False)
            else:
                importOriginals = promptYesNo(msg="Template file exists in the database, but does not\n" \
                    "appear to have any original strings. This could be as a result of a previous bad import.\n" \
                    "Do you wish to reimport the template file (with its original strings)?", default=True)
        else:
            self.__file = File()
            self.__file.setName(self.pot)
            self.__file.setProject(self.__project)
            self.__file.save()
            importOriginals = True
        if importOriginals:
            self.__importOriginals()
        
    
    def __initLanguage(self):
        "__initLanguage() -> Setup the language for the translations; prompt if necessary"
        if self.language_name:
            records = dbhelper.retrieve(Language, {Language.NAME_COL:self.language_name})
            if records:
                self.__language = records[0]
                return
        self.__language = promptLanguage(msg="Please select a language for the imported translations.")
        
    
    def __doPO(self):
        #check for existing translations
        results = dbhelper.executeQuery("select * from %s where %s in (select %s from %s where %s = %d)" % \
            (Translation.TABLE,Translation.ORIGINAL_ID_COL,Original.ID_COL, \
            Original.TABLE,Original.FILE_ID_COL,self.__file.id))
        if results:
            overwrite = promptYesNo(msg="Translated strings already exist in the database for this file.\n"\
                        "Do you wish to overwrite them (any existing translations in "\
                        "the database will be lost)?", default=False)
            if not overwrite:
                exit('Not overwriting existing translations.')
        #delete existing translations
        dbhelper.executeCustomDelete("delete from %s where %s in (select %s from %s where %s = %d)" % \
            (Translation.TABLE,Translation.ORIGINAL_ID_COL,Original.ID_COL, \
            Original.TABLE,Original.FILE_ID_COL,self.__file.id))
        #import translations
        file = open(self.po)
        po = pofile(file)
        file.close()
        for elem in po.poelements:  
            transObj = Translation()                          
            msgid = ' '.join([self.__cleanupString(s) for s in elem.msgid])
            if msgid == None or len(msgid) == 0:
                continue
            #get original - if not exist, WARN and skip
            records = dbhelper.retrieve(Original, {Original.RAW_COL:msgid,Original.FILE_ID_COL:self.__file.id})
            if records:
                transrecords = dbhelper.retrieve(Translation, {Translation.ORIGINAL_ID_COL:records[0].id})
                if transrecords:
                    transObj = transrecords[0]
                transObj.setOriginal(records[0])
                transObj.setLanguage(self.__language)            
                transObj.setRaw(' '.join([self.__cleanupString(s) for s in elem.msgstr]))
                transObj.setVersion('1.0')
                # TODO: calculate these somehow somewhere
                transObj.setDatefirst(DateTime(2004,1,1))
                transObj.save()
            else:
                print "\n\n******************  WARNING  ******************"
                print "Warning: msgid found in translated .po file, but not in database. This\n" + \
                    "probably means that it was not in the original template (.pot) file.\n" + \
                    "msgid : %s" % (msgid)                
                print "***********************************************"
        
        
    def process(self):
        "process() -> Run the import process"
        self.__doProject()
        self.__doFile()
        if self.translated:
            self.__initLanguage()
            self.__doPO()
        exit('Import completed successfully.')
        


def exit(msg=None):
    print ''
    if msg:        
        print msg
    print "Exiting"
    sys.exit('2')
    
def promptYesNo(msg,default=None):
    "promptYesNo(msg,default=None) -> Prompt for a yes/no answer, with an optional default"
    if default == None:
        allowed = ('Y','y','Yes','YES','yes','N','n','No','NO','no')
        message = msg + " (y/n) -> "
    else:
        allowed = ('Y','y','Yes','YES','yes','N','n','No','NO','no','')
        if default == True:
            message = msg + " (Y/n) -> "
        else:
            message = msg + " (y/N) -> "
    temp = prompt(msg=msg,name='Input',allowedValues=allowed)
    if temp in ('Y','y','Yes','YES'):
        return True
    if temp in ('N','n','No','NO','no'):
        return False
    if temp == '':
        return default
        

def promptLanguage(msg):
    "promptLanguage(msg) -> Prompt for a language"
    languages = dbhelper.retrieve(Language,{},[Language.NAME_COL])
    count = 0
    options = {}
    for language in languages:
        count = count + 1
        options[count] = language
    temp = None
    while temp == None:
        print ''
        print msg
        print "Valid options are:"
        print "\n".join(["%d. %s" % (num,language.name) for num,language in options.items()])
        print "Please enter the number corresponding to the language you want:"
        input = sys.stdin.readline().strip()
        if input == None:
            input = '0'  
        try:
            key = int(input)      
        except:
            print "Invalid input. Please try again."
            continue
        if not options.has_key(key):
            print "Invalid input. Please try again."
            continue
        else:
            temp = key
    return options[temp]
    
    
def promptFile(msg,name,mustExist=False,default=None):
    "promptFile(msg,name,mustExist=False,default=None) -> Prompt for a file with an optional default, and an optional constraint that the file exist."
    temp = None
    while temp == None:
        print ''
        print msg
        input = sys.stdin.readline().strip()
        if input == None:
            input = ''
        if len(input) == 0:
            if default != None:
                input = default
            else:
                print name + " must be specified."
                continue
        if mustExist:
            if not os.path.exists(input) or not os.path.isfile(input):
                print temp + " does not exist."
                continue
        temp = input
    return temp
    
    
def prompt(msg,name,min=0,max=9999,allowedValues=None):
    "prompt(msg,name,min=0,max=9999,allowedValues=None) -> Prompt for a string answer, with an optional default, optional min/max lengths, and an optional tuple of allowed values"
    temp = None
    while temp == None:
        print ''
        print msg
        input = sys.stdin.readline().strip()
        if input == None:
            input = ''
        if len(input) < min:
            print name + " length must be >= " + min
        elif len(input) > max:
            print name + " length must be <= " + max
        elif allowedValues != None and not input in allowedValues:
            print name + " must be one of [" + ", ".join(allowedValues) + "]"
        else:
            temp = input
    return temp
          
    
def usage():   
    "usage() -> print a usage info message" 
    print ''
    print "Usage: python Import.py [OPTIONS] [FILE]"
    print ""
    print "Options:"
    print "======="
    print "\t-p NAME, --project_name=NAME"
    print "\t\tThe name of the project into which the file is to be imported."
    print "\t\tThe project name and the project version (see below) uniquely identify"
    print "\t\tthe project."
    print ""
    print "\t-v VERSION, --project_version=VERSION"
    print "\t\tThe \"version\" of the project into which the file is to be imported."
    print "\t\tThe project name (see above) and the project version uniquely identify"
    print "\t\tthe project."
    print ""
    print "\t-a CHARACTER, --accel_char=CHARACTER"
    print "\t\tThe character used to indicate the accelerator key (mnemonic) in this project."
    print "\t\tThis argument is ignored unless a new project is to be created (see below)."
    print ""
    print "\t-f FILE, --template_file=FILE"
    print "\t\tThe .pot file. This option is used in one of two ways - when importing the .pot,"
    print "\t\tthis argument indicates which .pot to import. When importing a .po file of translations,"
    print "\t\tthis option specifies the .pot file for which the translations being imported."
    print ""
    print "\t-l LANGUAGE, --language=LANGUAGE"
    print "\t\tThe language for which we are importing translations. This option is ignored unless"
    print "\t\tthe -t option is specified."
    print ""
    print "\t-t, --translated"
    print "\t\tThis flag indicates that we are importing translations in the form of .po file."
    print "\t\tIf this optionis specified, the .po filename must follow be given (after all "
    print "\t\tother options)."
    print ""
    print "Notes:"
    print "====="
    print "\tIf the project name/version does not exist in the database, the user will be asked whether"
    print "\the/she wants it to be created. The project will be created with the accelerator character"
    print "\tspecified  with the -a option (or will prompted for the character, if it is not given). This"
    print "\tis the only time that the -a option is used."
    print ""
    print "\tIf -t is not given, the assumption is that the user wishes to import a template (.pot) file."
    print ""
    print "\tThis script is interactive. If any required options are not given on the command line, the user"
    print "\twill be prompted for them. The command line arguments provide a convenient way for project specific"
    print "\twrapper scripts to invoke the importer."
    print ""
    print "Examples:"
    print "========"
    print "\tpython Import.py -p 'KDE' -v '3.2' -a '_' -f filechooser.pot"
    print "\tImport the template file called filechooser.pot into project KDE (version 3.2). If the project"
    print "\tdoes not exist, the user will be prompted whether or not to create it (with accelerator"
    print "\tcharacter '_')."
    print ""
    print "\tpython Import.py -p 'KDE' -v '3.2' -f filechooser.pot -l 'Zulu' -t zu/filechooser.po"
    print "\tImport the Zulu translated .po file zu/filechooser.po into project KDE (version 3.2), and associate"
    print "\tit with the template file filechooser.pot"

def main():
    "main() -> the main method"
    import getopt    
    try:
        optlist,args = getopt.getopt(sys.argv[1:], 'p:v:a:l:f:t',['project_name=','project_version=','accel_char=','language=','template_file=','translated'])    
    except getopt.GetoptError:
        # print usage information and exit:
        usage()
        exit()
    importer = Importer()
    try:
        for option,value in optlist:
            if option in ("-p","--project_name"):
                importer.setProjectName(value)
            if option in ("-v","--project_version"):
                importer.setProjectVersion(value)
            if option in ("-a","--accel_char"):
                importer.setAccel(value)
            if option in ("-l","--language"):
                importer.setLanguageName(value)
            if option in ("-f","--template_file"):
                importer.setTemplate(value)
            if option in ("-t","--translated"):
                importer.setTranslated(True)
                importer.setTranslatedFile(args[0])
    except err:
        print err
        usage()
        exit()
    importer.process()
   
       
# This should go elsewhere. Useful, so for now it lives here.    
def printPO(po):
    "Dumps a pofile object to stdout"
    print '============================================='
    for prop in ('filename','sourceindex','msgindex'):
        try:            
            print prop + ' : ' + getattr(po, prop)
        except  AttributeError:
            print '\t' + prop + ' : None'
    for elem in po.poelements:
        print '============================================='
        print 'PO Element:'
        for prop in ('msgid','msgstr','sourcecomments','msgid_plural',
            'msgid_pluralcomments','othercomments','typecomments',
            'visiblecomments','msgidcomments'):
            try:            
                print '\t' + prop + ' : ' + '\n'.join(getattr(elem, prop))
            except AttributeError:
                print '\t' + prop + ' : None'
    print '============================================='
         
# Main ...
if __name__ == "__main__":
    main()
    fsock = open(filename)
    pp = pofile(fsock)
    printPO(pp)
    fsock.close()