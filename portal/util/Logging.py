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

"Utility code for logging inside webKit"
import sys
from time import *

LOG_LEVEL_SILENT=0
LOG_LEVEL_CRITICAL=1
LOG_LEVEL_ERROR=2
LOG_LEVEL_WARN=3
LOG_LEVEL_DEBUG=4

loglevel=LOG_LEVEL_ERROR
dest=sys.stdout

def debug(msg):
    log(LOG_LEVEL_DEBUG,"DEBUG (%s): " % (asctime(localtime())) + str(msg))
def warn(msg):
    log(LOG_LEVEL_WARN,"WARN  (%s): " % (asctime(localtime())) + str(msg))
def error(msg):
    log(LOG_LEVEL_ERROR,"ERROR (%s): " % (asctime(localtime())) + str(msg))
def critical(msg):
    log(LOG_LEVEL_CRITICAL,"CRITICAL (%s): " % (asctime(localtime())) + str(msg)) 
def log(level,msg):
    if loglevel >= level:
        dest.write(msg)
        dest.write("\n")
        dest.flush()
        