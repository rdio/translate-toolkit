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
try:
  import optparse
except ImportError:
  from translate.misc import optparse
from translate import __version__

norecursion = 0
optionalrecursion = 1
defaultrecursion = 2

# TODO: work out how to support .po/.pot differences

class ConvertOptionParser(optparse.OptionParser):
  """a specialized Option Parser for convertor tools..."""
  def __init__(self, recursion, inputformats, outputformats, usetemplates=False):
    """construct the specialized Option Parser"""
    optparse.OptionParser.__init__(self, version="%prog "+__version__.ver)
    self.usetemplates = usetemplates
    self.setrecursion(recursion)
    self.setinputformats(inputformats)
    self.setoutputformats(outputformats)
    self.usage = "%prog [options] " + " ".join([self.getusagestring(option) for option in self.option_list])

  def getusagestring(self, option):
    """returns the usage string for the given option"""
    optionstring = "|".join(option._short_opts + option._long_opts)
    if option.metavar:
      optionstring += " " + option.metavar
    return "[%s]" % optionstring

  def setrecursion(self, recursion):
    """sets the level of recursion supported by the parser..."""
    if recursion == defaultrecursion:
      self.argumentdesc = "dir"
    elif recursion == optionalrecursion:
      if self.has_option("-R"):
        self.remove_option("-R")
      self.add_option("-R", "--recursive", action="store_true", dest="recursion", default=False, \
        help="recurse subdirectories")
      self.argumentdesc = "file/dir"
    elif not recursion:
      self.argumentdesc = "file"
    else:
      raise ValueError("invalid recursion argument: %r" % recursion)
    self.recursion = recursion

  def define_option(self, option):
    """defines the given option, replacing an existing one of the same short name if neccessary..."""
    for short_opt in option._short_opts:
      if self.has_option(short_opt):
        self.remove_option(short_opt)
    for long_opt in option._long_opts:
      if self.has_option(long_opt):
        self.remove_option(long_opt)
    self.add_option(option)

  def setinputformats(self, inputformats):
    """sets the input formats to the given list/single string"""
    if isinstance(inputformats, basestring):
      inputformats = [inputformats]
    self.inputformats = inputformats
    inputformathelp = self.getformathelp(inputformats)
    inputoption = optparse.Option("-i", "--input", dest="input", default=None, metavar="INPUT",
                    help="read from INPUT %s in %s" % (self.argumentdesc, inputformathelp))
    self.define_option(inputoption)
    if self.usetemplates:
      templateoption = optparse.Option("-t", "--template", dest="template", default=None, metavar="TEMPLATE",
                    help="read from TEMPLATE %s in %s" % (self.argumentdesc, inputformathelp))
      self.define_option(templateoption)

  def setoutputformats(self, outputformats):
    """sets the output formats to the given list/single string"""
    if isinstance(outputformats, basestring):
      outputformats = [outputformats]
    self.outputformats = outputformats
    outputformathelp = self.getformathelp(outputformats)
    outputoption = optparse.Option("-o", "--output", dest="output", default=None, metavar="OUTPUT",
                    help="write to OUTPUT %s in %s" % (self.argumentdesc, outputformathelp))
    self.define_option(outputoption)

  def getformathelp(self, formats):
    """make a nice help string for describing formats..."""
    if len(formats) == 0:
      return ""
    elif len(formats) == 1:
      return "%s format" % (formats[0])
    else:
      return "%s formats" % (", ".join(formats))

  def getinputfile(self):
    """gets the input file defined by the options"""
    if self.input is None:
      return sys.stdin
    else:
      return open(self.input, 'r')

  def getoutputfile(self):
    """gets the output file defined by the options"""
    if self.output is None:
      return sys.stdout
    else:
      return open(self.output, 'w')

  def runconversion(self, convertmethod):
    """runs the conversion method using the given commandline options..."""
    if self.recursion:
      if self.input is None:
        raise optparse.OptionValueError("cannot use stdin for recursive run. please specify inputfile")
      if not os.path.isdir(self.input):
        raise optparse.OptionValueError("inputfile must be directory for recursive run.")
      if self.output is None:
        raise optparse.OptionValueError("must specify output directory for recursive run.")
      if not os.path.isdir(self.output):
        raise optparse.OptionValueError("output must be existing directory for recursive run.")
      # TODO: add recurseconversion method...
      self.recurseconversion(convertmethod)
    else:
      convertmethod(self.getinputfile(), self.getoutputfile())

