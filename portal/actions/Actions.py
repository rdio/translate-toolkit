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

"Action code for the translate portal"


from translate.portal.util import Logging
from translate.portal.util.HTTPUtil import *
from translate.portal.database.model import *
from translate.portal.database import dbhelper
def doTest(transaction):
    Logging.debug("Action doTest called.")
    
def doTranslationsave(transaction):
    Logging.debug("Action doTranslationsave called.")
    wrapper = HTTPRequestParameterWrapper(transaction.request())
    translationid = wrapper.getInt("translationid", -1)
    originalid = wrapper.getInt("originalid",-1)    
    languageid = wrapper.getInt("languageid",-1)
    raw = wrapper.getString("raw", "")
    translation =  None
    if translationid > 0:
        translation = dbhelper.fetchByPK(Translation,translationid)
    else:
        translation = Translation(
            {Translation.VERSION_COL:"1.0",
            Translation.ORIGINAL_ID_COL:originalid,
            Translation.LANGUAGE_ID_COL:languageid}
        )
    if translation:
        translation.setRaw(raw)
        translation.save()
        wrapper.set("original",translation.original.id)