#!/usr/bin/python2.2
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

"""tool to create the tables in the database"""

from translate.portal import config, portaldb
from jToolkit.data import database, dbtable
from jToolkit import errors
import sys

def getvalidconfigs():
  return ", ".join([configname for configname in dir(config) if not configname.startswith("_")])

def main(dbconfig, verbose):
  if verbose:
    tracefile = sys.stdout
  else:
    tracefile = None
  db = database.dbwrapper(dbconfig, errors.ConsoleErrorHandler(tracefile=tracefile))
  pdb = portaldb.portaldb(db)
  if pdb.createtables():
   print "created tables successfully"
  else:
    print "error creating tables"

if __name__ == '__main__':
  # handle command line options
  try:
    import optparse
  except ImportError:
    from translate.misc import optparse
  inputformat = "po"
  parser = optparse.OptionParser(usage="%prog [-d|--dbname databasename] [-v|--verbose]")
  parser.add_option("-d", "--dbname", dest="databasename", default="default",
                    help="create this database (valid options are: %s)" % getvalidconfigs(), metavar="databasename")
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="print trace messages to stdout")
  (options, args) = parser.parse_args()
  dbconfig = getattr(config, options.databasename, None)
  if dbconfig is None:
    raise ValueError("could not find dbname %s: value options are %r" % (dbconfig, getvalidconfigs()))
  main(dbconfig, options.verbose)

