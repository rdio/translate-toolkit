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

from translate.portal.BaseMVCServlet import BaseMVCServlet
#from translate.portal.web.actions import *
#from translate.portal.web.views import *

class index(BaseMVCServlet):
    pass