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

"""Base WebKit servlet for handling action/view type requests.
The basic idea is as follows:
 - the request data contains an optional action=xxx parameter. Acion 
 code corresponding to xxx is invoked by this servlet.
 - the request contains a view=yyy parameter. This is used to decide 
 what view object is written back to the browser. 
"""

from WebKit.HTTPServlet import HTTPServlet
from translate.portal.actions import Actions
from translate.portal.views import SetupView
from translate.portal.util import Logging

Logging.loglevel=Logging.LOG_LEVEL_DEBUG

class BaseMVCServlet(HTTPServlet):
        
    ACTION_FIELD_NAME = "action"
    VIEW_FIELD_NAME = "view"
    
    def respondToPost(self,transaction):
        "Handle POST's to this servlet"
        Logging.debug("Handling POST")
        self.__handleRequest(transaction)        
        
    def respondToGet(self,transaction):
        "Handle GET's to this servlet"     
        Logging.debug("Handling GET")     
        self.__handleRequest(transaction)

    def __handleRequest(self, transaction):
        "This method actually handles the request"        
        action = transaction.request().field(BaseMVCServlet.ACTION_FIELD_NAME, None)
        if action:
            action = "do" + action.capitalize()
            func = getattr(Actions,action,None)
            if callable(func):
                func(transaction)
            else:
                Logging.warn("Action %s not found." % str(action))
        else: Logging.debug("no action specified - skipping action invocation")
        
        view = transaction.request().field(BaseMVCServlet.VIEW_FIELD_NAME, None)         
        viewmodule = None
        try:
            viewmodule = __import__("translate.portal.views." + view,globals(),locals(),"translate.portal.views")               
        except ImportError:
            pass              
        Logging.debug("View Module: " + str(viewmodule))
        content = ""        
        if viewmodule:
            #get the template
            cls = getattr(viewmodule,view)
            if cls:
                tmpl = cls()
                #setup the template object (with values, etc)
                SetupView.setupGlobal(transaction,tmpl)
                setup = getattr(SetupView,"setup" + view.capitalize(),None)
                if callable(setup):
                    setup(transaction,tmpl)
                content = tmpl.respond()
            else:
                Logging.warn("View template (%s) not found" % (view))
        else:
            Logging.warn("View module (%s) not found" % (view))
        transaction.response().write(content)
        transaction.response().deliver()