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

"Utility code for aspects of HTTP parameter processing in the application"

class ParameterWrapper:
    "A simple wrapper around dict data"
    
    def __init__(self,values={}):
        self.__data = values
        
    def getInt(self,name,default=0):
        "Get the named field as an int"
        return int(self.getSingle(name,default))
    
    def getString(self,name,default=None):
        "Get the named field as a str"
        val = self.getSingle(name,default)
        return val and str(val) or default
    
    def getFloat(self,name,default=0):
        "Get the named field as a float"
        return float(self.getSingle(name,default))
    
    def getInts(self,name,default=[]):
        "Get the named field as a list of ints"
        val = self.getList(name,default)
        return [int(i) for i in val]
    
    def getStrings(self,name,default=[]):
        "Get the named field as a list of strs"
        val = self.getList(name,default)
        return [str(i) for i in val]
    
    def getFloats(self,name,default=[]):
        "Get the named field as a list of floats"
        val = self.getList(name,default)
        return [float(i) for i in val]
    
    def getSingle(self,name,default):
        "Get a single (the first) value for the named field"
        val = self.get(name,default)
        if val:
            if isinstance(val,list):
                return len(val) and val[0] or default
        return val
        
    def getList(self,name,default):
        "Get a list containing all the values for the named field"
        val = self.get(name,default)
        if not isinstance(val,list):
            if val == None: 
                return default
            else:
                return [val]
        return val
    
    def get(self,name,default):
        return self.__data.get(name,default)
        
    def containsKey(self, name):
        return self.__data.has_key(name)

    def set(self, name, value):
        self.__data[name] = value

    def delete(self, name):
        del self.__data[name]
        
    def __getitem__(self,name): 
        return self.__data[name]

    def __setitem__(self,name,value): 
        self.__data[name] = value
        
        
class HTTPRequestParameterWrapper(ParameterWrapper):
    "A wrapper around HTTP request field data"
    def __init__(self,request):
        ParameterWrapper.__init__(self,request.fields())
        
        
        
class SessionParameterWrapper(ParameterWrapper):
    "A wrapper around HTTP session data"
    def __init__(self,session):
        ParameterWrapper.__init__(self,session.values())