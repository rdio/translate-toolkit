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

"""script that converts a set of .po files to a set of .dtd and .properties files
either done using a template or just using the .po file"""

import os.path
import sys
from translate.convert import po2dtd
from translate.convert import po2prop
from translate.storage import xpi
from translate import __version__
from translate.convert import convert
import StringIO

class MozConvertOptionParser(convert.ArchiveConvertOptionParser):
  def __init__(self, formats, usetemplates=False, usepots=False, description=None):
    convert.ArchiveConvertOptionParser.__init__(self, formats, usetemplates, usepots, description=description, archiveformats={"xpi": xpi.XpiFile})

  def initoutputarchive(self, options):
    """creates an outputarchive if required"""
    if options.output and self.isarchive(options.output, mustexist=False):
      if self.isarchive(options.template):
        newlang = None
	newregion = None
	if options.locale is not None:
	  if options.locale.count("-") != 1:
	    raise ValueError("Invalid locale: %s - should be of the form xx-YY" % options.locale)
	  newlang, newregion = options.locale.split("-")
        options.outputarchive = options.templatearchive.clone(options.output, "a", newlang=newlang, newregion=newregion)
      else:
        if os.path.exists(options.output):
          options.outputarchive = xpi.XpiFile(options.output)
        else:
          options.outputarchive = xpi.XpiFile(options.output, "w")

  def recursiveprocess(self, options):
    """recurse through directories and convert files"""
    result = super(MozConvertOptionParser, self).recursiveprocess(options)
    if self.isarchive(options.output):
      if options.progress in ('console', 'verbose'):
        print "writing xpi file..."
      options.outputarchive.close()
    return result

def main():
  # handle command line options
  formats = {("dtd.po", "dtd"): ("dtd", po2dtd.convertdtd),
             ("properties.po", "properties"): ("properties", po2prop.convertprop),
             (None, "*"): ("*", convert.copytemplate),
             ("*", "*"): ("*", convert.copyinput),
             "*": ("*", convert.copyinput)}
  parser = MozConvertOptionParser(formats, usetemplates=True, description=__doc__)
  parser.add_option("-l", "--locale", dest="locale", default=None,
    help="set output locale (required as this sets the directory names)", metavar="LOCALE")
  parser.run()

