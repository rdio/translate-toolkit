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

import sys
import os.path
from translate.misc import optrecurse
from translate import __version__
try:
  from cStringIO import StringIO
except ImportError:
  from StringIO import StringIO

class ConvertOptionParser(optrecurse.RecursiveOptionParser, object):
  """a specialized Option Parser for convertor tools..."""
  def __init__(self, formats, usetemplates=False, usepots=False, description=None):
    """construct the specialized Option Parser"""
    optrecurse.RecursiveOptionParser.__init__(self, formats, usetemplates, description=description)
    self.usepots = usepots
    self.setpotoption()
    self.set_usage()

  def potifyformat(self, fileformat):
    """converts a .po to a .pot where required"""
    if fileformat is None:
      return fileformat
    elif fileformat == "po":
      return "pot"
    elif fileformat.endswith(os.extsep + "po"):
      return fileformat + "t"
    else:
      return fileformat

  def getformathelp(self, formats):
    """make a nice help string for describing formats..."""
    # include implicit pot options...
    helpformats = []
    for fileformat in formats:
      helpformats.append(fileformat)
      potformat = self.potifyformat(fileformat)
      if potformat != fileformat:
        helpformats.append(potformat)
    return super(ConvertOptionParser, self).getformathelp(helpformats)

  def filterinputformats(self, options):
    """filters input formats, processing relevant switches in options"""
    if self.usepots and options.pot:
      return [self.potifyformat(inputformat) for inputformat in self.inputformats]
    else:
      return self.inputformats

  def filteroutputoptions(self, options):
    """filters output options, processing relevant switches in options"""
    if self.usepots and options.pot:
      outputoptions = {}
      for (inputformat, templateformat), (outputformat, convertor) in self.outputoptions.iteritems():
        inputformat = self.potifyformat(inputformat)
        templateformat = self.potifyformat(templateformat)
        outputformat = self.potifyformat(outputformat)
        outputoptions[(inputformat, templateformat)] = (outputformat, convertor)
      return outputoptions
    else:
      return self.outputoptions

  def setpotoption(self):
    """sets the -P/--pot option depending on input/output formats etc"""
    if self.usepots:
      potoption = optrecurse.optparse.Option("-P", "--pot", \
                      action="store_true", dest="pot", default=False, \
                      help="use PO template files (.pot) rather than PO files (.po)")
      self.define_option(potoption)

  def run(self):
    """parses the command line options and runs the conversion"""
    (options, args) = self.parse_args()
    options.inputformats = self.filterinputformats(options)
    options.outputoptions = self.filteroutputoptions(options)
    self.recursiveprocess(options)

def copyinput(inputfile, outputfile, templatefile, **kwargs):
  """copies the input file to the output file"""
  outputfile.write(inputfile.read())
  outputfile.close()
  return True

def copytemplate(inputfile, outputfile, templatefile, **kwargs):
  """copies the template file to the output file"""
  outputfile.write(templatefile.read())
  outputfile.close()
  return True
  
