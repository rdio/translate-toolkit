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
      self.add_option("-R", "--recursive", action="store_true", dest="recursive", default=False, \
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

  def getinputfile(self, options):
    """gets the input file defined by the options"""
    if options.input is None:
      return sys.stdin
    else:
      return open(options.input, 'r')

  def getoutputfile(self, options):
    """gets the output file defined by the options"""
    if options.output is None:
      return sys.stdout
    else:
      return open(options.output, 'w')

  def runconversion(self, options, convertmethod):
    """runs the conversion method using the given commandline options..."""
    if (self.recursion == optionalrecursion and options.recursive) or (self.recursion == defaultrecursion):
      if options.input is None:
        self.error(optparse.OptionValueError("cannot use stdin for recursive run. please specify inputfile"))
      if not os.path.isdir(options.input):
        self.error(optparse.OptionValueError("inputfile must be directory for recursive run."))
      if options.output is None:
        self.error(optparse.OptionValueError("must specify output directory for recursive run."))
      if not os.path.isdir(options.output):
        self.error(optparse.OptionValueError("output must be existing directory for recursive run."))
      self.recurseconversion(options)
    else:
      convertmethod(self.getinputfile(options), self.getoutputfile(options))

  def recurseconversion(self, options):
    """recurse through directories and convert files"""
    # TODO: refactor this, it's too long...
    dirstack = ['']
    # discreated contains all the directories created, mapped to whether they've been used or not...
    dirscreated = {}
    while dirstack:
      top = dirstack.pop(-1)
      names = os.listdir(os.path.join(options.input, top))
      dirs = []
      for name in names:
        inputname = os.path.join(options.input, top, name)
        # handle directories...
        if os.path.isdir(inputname):
          dirs.append(os.path.join(top, name))
          outputname = os.path.join(options.output, top, name)
          if not os.path.isdir(outputname):
            os.mkdir(outputname)
            dirscreated[dirs[-1]] = 0
            if top in dirscreated:
              dirscreated[top] = 1
          if self.usetemplates and options.template:
            templatename = os.path.join(options.template, top, name)
            if not os.path.isdir(templatename):
              print >>sys.stderr, "warning: missing template directory %s" % templatename
        elif os.path.isfile(inputname):
          base, inputext = os.path.splitext(name)
          inputext = inputext.replace(os.extsep, "", 1)
          if not inputext in self.inputformats:
            # only handle names that match recognized input file extensions
            continue
          # now we have split off .po, we split off the original extension
          outputname = os.path.join(options.output, top, self.getoutputname(name))
          inputfile = open(inputname, 'r')
          outputfile = open(outputname, 'w')
          templatefile = None
          if self.usetemplates and options.template:
            templatename = os.path.join(options.template, top, name)
            if os.path.isfile(templatename):
              templatefile = open(templatename, 'r')
            else:
              print >>sys.stderr, "warning: missing template file %s" % templatename
          convertmethod = self.inputformats[inputext]
          if convertmethod(inputfile, outputfile, templatefile):
            if top in dirscreated:
              dirscreated[top] = 1
          else:
            outputfile.close()
            os.unlink(outputname)
      # make sure the directories are processed next time round...
      dirs.reverse()
      dirstack.extend(dirs)
    # remove any directories we created unneccessarily
    # note that if there is a tree of empty directories, only leaves will be removed...
    for createddir, used in dirscreated.iteritems():
      if not used:
        os.rmdir(os.path.join(options.output, createddir))

  def getoutputname(self, inputname):
    """gets an output filename based on the input filename"""
    # TODO: handle replacing the input extension...
    return inputname + os.extsep + self.outputformats[0]

