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

"""connection settings for the translate portal database.
Dictionary elements correspond to connection settings as per the pygresql
options.
i.e.
    dbname        - name of connected database (string/None)
    host          - name of the server host (string/None)
    port          - port used by the database server (integer/-1)
    opt           - connection options (string/None)
    tty           - debug terminal (string/None)
	user          - PostgreSQL user (string/None)
    passwd        - password for user (string/None)
    
In addition, there are the following options that 
configure the size and behaviour of the connection pool:
    minpoolsize      - the minimum size of the pool 
    maxpoolsize      - the maximum size of the pool
"""

connectionParams={ 
    "host":"localhost",
    "user":"postgres",
    "passwd":"",
    "dbname":"translate",
    "minpoolsize":"4",
    "maxpoolsize":"12"
}