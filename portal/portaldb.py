#!/usr/bin/env python
# 
# Copyright 2002, 2003 Zuza Software Foundation
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

"""classes that handle storage of translations in a database"""

from jToolkit.data import dbtable, dates

class portaldb:
  def __init__(self, db, errorhandler = None):
    self.db = db
    if errorhandler is None: errorhandler = self.db.errorhandler
    self.errorhandler = errorhandler
    number, string, datetime, text = "number", "string", "datetime", "text"
    self.sourcefiles = dbtable.DBTable(db, "sourcefiles",
      [("fileid", number), ("filename", string)],
      ["fileid"], ["filename"])
    self.stringversions = dbtable.DBTable(db, "stringversions",
      [("stringversionid", number), ("fileid", number), ("originalid", number),
       ("versionname", string), ("versiontype", string)],
       ["stringversionid"], ["versionname"])
    self.original = dbtable.DBTable(db, "original",
      [("originalid", number), ("location", string), ("originalstring", text)],
      ["originalid", "location"], [])
    self.translation = dbtable.DBTable(db, "translation",
      [("translationid", number), ("language", string), ("originalid", number),
       ("translationstring", text), ("created", datetime)],
      ["translationid"], [])
    self.state = dbtable.DBTable(db, "state",
      [("translationid", number), ("stateid", number),
       ("statestart", datetime), ("stateend", datetime), ("statefrom", number)],
      ["translationid", "statestart"], [])
    self.statetype = dbtable.DBTable(db, "statetype",
      [("stateid", number), ("statename", string), ("rank", number)],
      ["stateid"], [])
    self.tables = dict([(table.tablename, table) for table in 
                        (self.sourcefiles, self.stringversions, self.original, self.translation,
                         self.state, self.statetype)])

  def createtables(self):
    success = 1
    for tablename, table in self.tables.iteritems():
      if not table.createtable():
        print "error creating %s" % tablename
        success = 0
    return success

  def droptables(self):
    success = 1
    for tablename, table in self.tables.iteritems():
      if not table.droptable():
        print "error dropping %s" % tablename
        success = 0
    return success

  def addsourcefile(self, filename):
    """adds the source file, if it does not exist, returns the fileid"""
    filefilter = "where filename='%s'" % filename
    filenameexists = self.sourcefiles.filtermatchessome(filefilter)
    if filenameexists:
      fileid = self.sourcefiles.getsomerecord(filefilter)['fileid']
    else:
      fileid = 78
      self.sourcefiles.addrow({'fileid':fileid, 'filename':filename})
    return fileid

