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
from translate.misc import progressbar
from translate import __version__

norecursion = 0
optionalrecursion = 1
defaultrecursion = 2

# TODO: handle input/output without needing -i/-o
# TODO: refactor this and filters.filtercmd so they share code

class ConvertOptionParser(optparse.OptionParser):
  """a specialized Option Parser for convertor tools..."""
  def __init__(self, recursion, inputformats, outputformats, usetemplates=False, usepots=False, templateslikeinput=None):
    """construct the specialized Option Parser"""
    optparse.OptionParser.__init__(self, version="%prog "+__version__.ver)
    self.usepots = usepots
    self.setrecursion(recursion)
    self.setinputformats(inputformats)
    self.setoutputformats(outputformats)
    self.settemplatehandling(usetemplates, templateslikeinput)
    self.setprogressoptions()
    if self.usepots:
      self.setpotoption()
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

  def setoutputformats(self, outputformats):
    """sets the output formats to the given list/single string"""
    if isinstance(outputformats, basestring):
      outputformats = [outputformats]
    self.outputformats = outputformats
    outputformathelp = self.getformathelp(outputformats)
    outputoption = optparse.Option("-o", "--output", dest="output", default=None, metavar="OUTPUT",
                    help="write to OUTPUT %s in %s" % (self.argumentdesc, outputformathelp))
    self.define_option(outputoption)

  def settemplatehandling(self, usetemplates, templateslikeinput):
    """works out how to handle templates"""
    self.usetemplates = usetemplates
    if not self.usetemplates: return
    if templateslikeinput is None:
      self.templateslikeinput = not isinstance(self.outputformats, dict)
    else:
      self.templateslikeinput = templateslikeinput
    if self.templateslikeinput:
      templateformathelp = self.getformathelp(self.inputformats)
    else:
      templateformathelp = self.getformathelp(self.outputformats)
    templateoption = optparse.Option("-t", "--template", dest="template", default=None, metavar="TEMPLATE",
                  help="read from TEMPLATE %s in %s" % (self.argumentdesc, templateformathelp))
    self.define_option(templateoption)

  def setprogressoptions(self):
    """sets the progress options depending on recursion etc"""
    self.progresstypes = {"none": progressbar.NoProgressBar, "simple": progressbar.SimpleProgressBar,
                          "console": progressbar.ConsoleProgressBar, "curses": progressbar.CursesProgressBar,
                          "verbose": progressbar.VerboseProgressBar}
    progressoption = optparse.Option(None, "--progress", dest="progress", default="console",
                      choices = self.progresstypes.keys(), metavar="PROGRESS",
                      help="set progress type to one of %s" % (", ".join(self.progresstypes)))
    self.define_option(progressoption)

  def setpotoption(self):
    """sets the -P/--pot option depending on input/output formats etc"""
    if self.usepots:
      if "po" in self.inputformats:
        potoption = optparse.Option("-P", "--pot", action="store_true", dest="pot", default=False, \
                                   help="use PO template files (.pot) as input")
      elif "po" in self.outputformats:
        potoption = optparse.Option("-P", "--pot", action="store_true", dest="pot", default=False, \
                                   help="use PO template files (.pot) in output")
      else:
        potoption = optparse.Option("-P", "--pot", action="store_true", dest="pot", default=False, \
                                   help="use PO template files (.pot)")
      self.define_option(potoption)

  def getformathelp(self, formats):
    """make a nice help string for describing formats..."""
    if self.usepots and "po" in formats:
      if isinstance(formats, dict):
        formats["pot"] = formats["po"]
      else:
        formats.append("pot")
    if len(formats) == 0:
      return ""
    elif len(formats) == 1:
      return "%s format" % (", ".join(formats))
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

  def gettemplatefile(self, options):
    """gets the template file defined by the options"""
    if self.usetemplates and options.template:
      return open(options.template, 'r')
    return None

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
      convertmethod(self.getinputfile(options), self.getoutputfile(options), self.gettemplatefile(options))

  def getconvertmethod(self, inputext, outputext):
    """works out which conversion method to use..."""
    if isinstance(self.inputformats, dict):
      return self.inputformats[inputext]
    elif isinstance(self.outputformats, dict):
      return self.outputformats[outputext]
    else:
      raise ValueError("one of input/output formats must be a dict: %r, %r" % (self.inputformats, self.outputformats))

  def initprogressbar(self, allfiles, options):
    """sets up a progress bar appropriate to the options and files"""
    if options.progress in ('console', 'curses', 'verbose'):
      # iterate through the files and produce a list so we can show progress...
      allfiles = [inputfile for inputfile in allfiles]
      self.progressbar = self.progresstypes[options.progress](0, len(allfiles))
      print "processing %d files..." % len(allfiles)
    else:
      self.progressbar = self.progresstypes[options.progress]()
    return allfiles

  def recurseconversion(self, options):
    """recurse through directories and convert files"""
    join = os.path.join
    allfiles = self.recursefiles(options)
    allfiles = self.initprogressbar(allfiles, options)
    for inputext, inputpath, outputext, outputpath, templatepath in allfiles:
      convertmethod = self.getconvertmethod(inputext, outputext)
      fullinputpath = join(options.input, inputpath)
      fulloutputpath = join(options.output, outputpath)
      if templatepath is  None:
        fulltemplatepath = None
      else:
        fulltemplatepath = join(options.template, templatepath)
      success = self.convertfile(convertmethod, fullinputpath, fulloutputpath, fulltemplatepath)
      if success:
        outputsubdir = os.path.dirname(outputpath)
        self.usesubdir(outputsubdir)
      self.reportprogress(inputpath, success)
    self.prunesubdirs(options)
    del self.progressbar

  def convertfile(self, convertmethod, fullinputpath, fulloutputpath, fulltemplatepath):
    """run an invidividual conversion"""
    tempoutput = False
    if fulloutputpath == fullinputpath:
      tempoutput = True
      origoutputpath = fulloutputpath
      fulloutputpath += os.extsep + "tmp"
    if fulloutputpath == fulltemplatepath:
      tempoutput = True
      origoutputpath = fulloutputpath
      fulloutputpath += os.extsep + "tmp"
    inputfile = open(fullinputpath, 'r')
    outputfile = open(fulloutputpath, 'w')
    templatefile = None
    if fulltemplatepath is not None:
      if os.path.isfile(fulltemplatepath):
        templatefile = open(fulltemplatepath, 'r')
      else:
        print >>sys.stderr, "warning: missing template file %s" % fulltemplatepath
    if convertmethod(inputfile, outputfile, templatefile):
      if tempoutput:
        outputfile.close()
        os.unlink(origoutputpath)
        os.rename(fulloutputpath, origoutputpath)
      return True
    else:
      outputfile.close()
      os.unlink(fulloutputpath)
      return False

  def reportprogress(self, filename, success):
    """shows that we are progressing..."""
    self.progressbar.amount += 1
    if success:
      self.progressbar.show(filename)
    
  def checksubdir(self, parent, subdir):
    """checks to see if subdir under parent needs to be created, creates if neccessary"""
    fullpath = os.path.join(parent, subdir)
    if not os.path.isdir(fullpath):
      os.mkdir(fullpath)
      self.dirscreated[subdir] = 0
      subparent = os.path.dirname(subdir)
      if subparent in self.dirscreated:
        self.dirscreated[subparent] = 1

  def usesubdir(self, subdir):
    """indicates that the given directory was used..."""
    if subdir in self.dirscreated:
      self.dirscreated[subdir] = 1

  def prunesubdirs(self, options):
    """prunes any directories that were created unneccessarily"""
    # remove any directories we created unneccessarily
    # note that if there is a tree of empty directories, only leaves will be removed...
    for createddir, used in self.dirscreated.iteritems():
      if not used:
        os.rmdir(os.path.join(options.output, createddir))

  def recursefiles(self, options):
    """recurse through directories and return files to be converted..."""
    dirstack = ['']
    # discreated contains all the directories created, mapped to whether they've been used or not...
    self.dirscreated = {}
    join = os.path.join
    while dirstack:
      top = dirstack.pop(-1)
      names = os.listdir(join(options.input, top))
      dirs = []
      for name in names:
        inputpath = join(top, name)
        fullinputpath = join(options.input, inputpath)
        # handle directories...
        if os.path.isdir(fullinputpath):
          dirs.append(inputpath)
          self.checksubdir(options.output, inputpath)
          if self.usetemplates and options.template:
            fulltemplatepath = join(options.template, inputpath)
            if not os.path.isdir(fulltemplatepath):
              print >>sys.stderr, "warning: missing template directory %s" % fulltemplatepath
        elif os.path.isfile(fullinputpath):
          if not self.isvalidinputname(options, name):
            # only handle names that match recognized input file extensions
            continue
          # now we have split off .po, we split off the original extension
          outputname = self.getoutputname(options, name)
          outputbase, outputext = os.path.splitext(outputname)
          outputext = outputext.replace(os.extsep, "", 1)
          outputpath = join(top, outputname)
          templatepath = None
          if self.usetemplates and options.template:
            templatename = self.gettemplatename(options, name)
            templatepath = join(top, templatename)
          inputbase, inputext = os.path.splitext(name)
          inputext = inputext.replace(os.extsep, "", 1)
          yield (inputext, inputpath, outputext, outputpath, templatepath)
      # make sure the directories are processed next time round...
      dirs.reverse()
      dirstack.extend(dirs)

  def gettemplatename(self, options, inputname):
    """gets an output filename based on the input filename"""
    if self.templateslikeinput:
      return inputname
    else:
      outputname = self.getoutputname(options, inputname)
      # TODO: clean this up
      # templates should be pot files sometimes...
      outputbase, outputext = os.path.splitext(outputname)
      if outputext == os.extsep + "po":
        return outputbase + os.extsep + "pot"
      return outputname

  def getoutputname(self, options, inputname):
    """gets an output filename based on the input filename"""
    inputbase, ext = os.path.splitext(inputname)
    outputformat = iter(self.outputformats).next()
    if self.usepots and options.pot and outputformat == "po":
      outputformat = "pot"
    return inputbase + os.extsep + outputformat

  def isvalidinputname(self, options, inputname):
    """checks if this is a valid input filename"""
    inputbase, inputext = os.path.splitext(inputname)
    inputext = inputext.replace(os.extsep, "", 1)
    if self.usepots and options.pot and inputext == "pot":
      inputext = "po"
    return inputext in self.inputformats

class ConvertOptionParserExt(ConvertOptionParser):
  """an extended ConvertOptionParser that does clever things with input and output formats"""
  def getoutputname(self, options, inputname):
    """gets an output filename based on the input filename"""
    if isinstance(self.outputformats, dict):
      # if there is a dictionary of outputformats, assume it is encoded in the inputname...
      inputbase, ext = os.path.splitext(inputname)
      return inputbase
    else:
      outputformat = self.outputformats[0]
      if self.usepots and options.pot and outputformat == "po":
        outputformat = "pot"
      return inputname + os.extsep + outputformat

  def isvalidinputname(self, options, inputname):
    """checks if this is a valid input filename"""
    inputbase, inputext = os.path.splitext(inputname)
    inputext = inputext.replace(os.extsep, "", 1)
    if self.usepots and options.pot and inputext == "pot":
      inputext = "po"
    if isinstance(self.outputformats, dict):
      # if there is a dictionary of outputformats, check that the right format is encoded in the name...
      outputbase, outputext = os.path.splitext(inputbase)
      outputext = outputext.replace(os.extsep, "", 1)
      return inputext in self.inputformats and outputext in self.outputformats
    else:
      return inputext in self.inputformats

