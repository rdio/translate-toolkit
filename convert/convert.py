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

from __future__ import generators
import sys
import os.path
try:
  import optparse
except ImportError:
  from translate.misc import optparse
from translate.misc import progressbar
from translate import __version__
try:
  from cStringIO import StringIO
except ImportError:
  from StringIO import StringIO

# TODO: refactor this and filters.filtercmd so they share code

class ConvertOptionParser(optparse.OptionParser, object):
  """a specialized Option Parser for convertor tools..."""
  def __init__(self, inputformats, outputformats, usetemplates=False, usepots=False, templateslikeinput=None):
    """construct the specialized Option Parser"""
    optparse.OptionParser.__init__(self, version="%prog "+__version__.ver)
    self.usepots = usepots
    self.setprogressoptions()
    if self.usepots:
      self.setpotoption(inputformats, outputformats)
    self.setinputformats(inputformats)
    self.setoutputformats(outputformats)
    self.settemplatehandling(usetemplates, templateslikeinput)
    self.convertparameters = []
    self.usage = "%prog [options] " + " ".join([self.getusagestring(option) for option in self.option_list])

  def getusagestring(self, option):
    """returns the usage string for the given option"""
    optionstring = "|".join(option._short_opts + option._long_opts)
    if getattr(option, "optionalswitch", False):
      optionstring = "[%s]" % optionstring
    if option.metavar:
      optionstring += " " + option.metavar
    if getattr(option, "required", False):
      return optionstring
    else:
      return "[%s]" % optionstring

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
    if isinstance(inputformats, (str, unicode)):
      inputformats = [inputformats]
    self.inputformats = inputformats
    inputformathelp = self.getformathelp(inputformats)
    inputoption = optparse.Option("-i", "--input", dest="input", default=None, metavar="INPUT",
                    help="read from INPUT in %s" % (inputformathelp))
    inputoption.optionalswitch = True
    inputoption.required = True
    self.define_option(inputoption)

  def setoutputformats(self, outputformats):
    """sets the output formats to the given list/single string"""
    if isinstance(outputformats, (str, unicode)):
      outputformats = [outputformats]
    self.outputformats = outputformats
    outputformathelp = self.getformathelp(outputformats)
    outputoption = optparse.Option("-o", "--output", dest="output", default=None, metavar="OUTPUT",
                    help="write to OUTPUT in %s" % (outputformathelp))
    outputoption.optionalswitch = True
    outputoption.required = True
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
                  help="read from TEMPLATE in %s" % (templateformathelp))
    self.define_option(templateoption)

  def setprogressoptions(self):
    """sets the progress options"""
    self.progresstypes = {"none": progressbar.NoProgressBar, "simple": progressbar.SimpleProgressBar,
                          "console": progressbar.ConsoleProgressBar, "curses": progressbar.CursesProgressBar,
                          "verbose": progressbar.VerboseProgressBar}
    progressoption = optparse.Option(None, "--progress", dest="progress", default="console",
                      choices = self.progresstypes.keys(), metavar="PROGRESS",
                      help="set progress type to one of %s" % (", ".join(self.progresstypes)))
    self.define_option(progressoption)

  def setpotoption(self, inputformats, outputformats):
    """sets the -P/--pot option depending on input/output formats etc"""
    if self.usepots:
      if "po" in inputformats:
        potoption = optparse.Option("-P", "--pot", action="store_true", dest="pot", default=False, \
                                   help="use PO template files (.pot) as input")
      elif "po" in outputformats:
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

  def isrecursive(self, fileoption):
    """checks if fileoption is a recursive file"""
    if fileoption is None:
      return False
    elif isinstance(fileoption, list):
      return True
    else:
      return os.path.isdir(fileoption)

  def runconversion(self):
    """parses the command line options and runs the conversion"""
    (options, args) = self.parse_args()
    # some intelligent as to what reasonable people might give on the command line
    if args and not options.input:
      if len(args) > 1:
        options.input = args[:-1]
        args = args[-1:]
      else:
        options.input = args[0]
        args = []
    if args and not options.output:
      options.output = args[-1]
      args = args[:-1]
    if args:
      self.error("You have used an invalid combination of --input, --output and freestanding args")
    if isinstance(options.input, list) and len(options.input) == 1:
      options.input = options.input[0]
    try:
      self.recurseconversion(options)
    except optparse.OptParseError, message:
      self.error(message)

  def getrequiredoptions(self, options):
    """get the options required to pass to the filtermethod..."""
    requiredoptions = {}
    for optionname in dir(options):
      if optionname in self.convertparameters:
        requiredoptions[optionname] = getattr(options, optionname)
    return requiredoptions

  def getconvertmethod(self, inputpath, outputpath):
    """works out which conversion method to use..."""
    if inputpath:
      inputbase, inputext = os.path.splitext(inputpath)
      inputext = inputext.replace(os.extsep, "", 1)
    else:
      inputext = None
    if outputpath:
      outputbase, outputext = os.path.splitext(outputpath)
      outputext = outputext.replace(os.extsep, "", 1)
    else:
      outputext = None
    if isinstance(self.inputformats, dict):
      if not inputext:
        return self.inputformats.itervalues().next()
      else:
        return self.inputformats[inputext]
    elif isinstance(self.outputformats, dict):
      if not outputext:
        return self.outputformats.itervalues().next()
      else:
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

  def getfullinputpath(self, options, inputpath):
    """gets the absolute path to an input file"""
    if options.input:
      return os.path.join(options.input, inputpath)
    else:
      return inputpath

  def getfulloutputpath(self, options, outputpath):
    """gets the absolute path to an output file"""
    if options.recursiveoutput and options.output:
      return os.path.join(options.output, outputpath)
    else:
      return outputpath

  def getfulltemplatepath(self, options, templatepath):
    """gets the absolute path to a template file"""
    if not options.recursivetemplate:
      return templatepath
    elif templatepath is not None and self.usetemplates and options.template:
      return os.path.join(options.template, templatepath)
    else:
      return None

  def recurseconversion(self, options):
    """recurse through directories and convert files"""
    if self.isrecursive(options.input):
      if not self.isrecursive(options.output):
        self.error(optparse.OptionValueError("Cannot have recursive input and non-recursive output. check output exists"))
      if isinstance(options.input, list):
        allfiles = self.recursefilelist(options)
      else:
        allfiles = self.recursefiles(options)
    else:
      if options.input:
        allfiles = [os.path.basename(options.input)]
        options.input = os.path.dirname(options.input)
    options.recursiveoutput = self.isrecursive(options.output)
    options.recursivetemplate = self.usetemplates and self.isrecursive(options.template)
    allfiles = self.initprogressbar(allfiles, options)
    for inputpath in allfiles:
      fullinputpath = self.getfullinputpath(options, inputpath)
      outputpath = self.getoutputname(options, inputpath)
      fulloutputpath = self.getfulloutputpath(options, outputpath)
      if options.recursiveoutput and outputpath:
        self.checksubdir(options.output, os.path.dirname(outputpath))
      templatepath = self.gettemplatename(options, inputpath)
      fulltemplatepath = self.getfulltemplatepath(options, templatepath)
      convertmethod = self.getconvertmethod(fullinputpath, fulloutputpath)
      success = self.convertfile(convertmethod, options, fullinputpath, fulloutputpath, fulltemplatepath)
      self.reportprogress(inputpath, success)
    del self.progressbar

  def openinputfile(self, options, fullinputpath):
    """opens the input file"""
    if fullinputpath is None:
      return sys.stdin
    return open(fullinputpath, 'r')

  def openoutputfile(self, options, fulloutputpath):
    """opens the output file"""
    if fulloutputpath is None:
      return sys.stdout
    return open(fulloutputpath, 'w')

  def opentempoutputfile(self, options, fulloutputpath):
    """opens a temporary output file"""
    return StringIO()

  def finalizetempoutputfile(self, options, outputfile, fulloutputpath):
    """write the temp outputfile to its final destination"""
    outputfile.reset()
    outputstring = outputfile.read()
    outputfile = self.openoutputfile(options, fulloutputpath)
    outputfile.write(outputstring)
    outputfile.close()

  def opentemplatefile(self, options, fulltemplatepath):
    """opens the template file (if required)"""
    if fulltemplatepath is not None:
      if os.path.isfile(fulltemplatepath):
        return open(fulltemplatepath, 'r')
      else:
        print >>sys.stderr, "warning: missing template file %s" % fulltemplatepath
    return None

  def convertfile(self, convertmethod, options, fullinputpath, fulloutputpath, fulltemplatepath):
    """run an invidividual conversion"""
    inputfile = self.openinputfile(options, fullinputpath)
    if fulloutputpath and fulloutputpath in (fullinputpath, fulltemplatepath):
      outputfile = self.opentempoutputfile(options, fulloutputpath)
      tempoutput = True
    else:
      outputfile = self.openoutputfile(options, fulloutputpath)
      tempoutput = False
    templatefile = self.opentemplatefile(options, fulltemplatepath)
    requiredoptions = self.getrequiredoptions(options)
    if convertmethod(inputfile, outputfile, templatefile, **requiredoptions):
      if tempoutput:
        self.finalizetempoutputfile(options, outputfile, fulloutputpath)
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

  def mkdir(self, parent, subdir):
    """makes a subdirectory (recursively if neccessary)"""
    if not os.path.isdir(parent):
      raise ValueError("cannot make child directory %r if parent %r does not exist" % (subdir, parent))
    currentpath = parent
    subparts = subdir.split(os.sep)
    for part in subparts:
      currentpath = os.path.join(currentpath, part)
      if not os.path.isdir(currentpath):
        os.mkdir(currentpath)

  def checksubdir(self, parent, subdir):
    """checks to see if subdir under parent needs to be created, creates if neccessary"""
    fullpath = os.path.join(parent, subdir)
    if not os.path.isdir(fullpath):
      self.mkdir(parent, subdir)

  def recursefilelist(self, options):
    """use a list of files, and find a common base directory for them"""
    # find a common base directory for the files to do everything relative to
    commondir = os.path.dirname(os.path.commonprefix(options.input))
    allfiles = []
    for inputfile in options.input:
      if inputfile.startswith(commondir+os.sep):
        allfiles.append(inputfile.replace(commondir+os.sep, "", 1))
      else:
        allfiles.append(inputfile.replace(commondir, "", 1))
    options.input = commondir
    return allfiles

  def recursefiles(self, options):
    """recurse through directories and return files to be converted..."""
    dirstack = ['']
    join = os.path.join
    while dirstack:
      top = dirstack.pop(-1)
      names = os.listdir(join(options.input, top))
      dirs = []
      for name in names:
        inputpath = join(top, name)
        fullinputpath = self.getfullinputpath(options, inputpath)
        # handle directories...
        if os.path.isdir(fullinputpath):
          dirs.append(inputpath)
          fulltemplatepath = self.getfulltemplatepath(options, inputpath)
          if fulltemplatepath and not os.path.isdir(fulltemplatepath):
              print >>sys.stderr, "warning: missing template directory %s" % fulltemplatepath
        elif os.path.isfile(fullinputpath):
          if not self.isvalidinputname(options, name):
            # only handle names that match recognized input file extensions
            continue
          yield inputpath
      # make sure the directories are processed next time round...
      dirs.reverse()
      dirstack.extend(dirs)

  def gettemplatename(self, options, inputname):
    """gets an output filename based on the input filename"""
    if self.usetemplates and options.template:
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
    else:
      return None

  def getoutputname(self, options, inputname):
    """gets an output filename based on the input filename"""
    if not inputname or not options.recursiveoutput: return options.output
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
    if not inputname or not options.recursiveoutput: return options.output
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

