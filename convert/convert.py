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
  if optparse.__version__ < "1.4.1+":
    raise ImportError("optparse version not compatible")
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
  def __init__(self, formats, usetemplates=False, usepots=False):
    """construct the specialized Option Parser"""
    optparse.OptionParser.__init__(self, version="%prog "+__version__.ver)
    self.usepots = usepots
    self.setprogressoptions()
    self.setpotoption()
    self.setformats(formats, usetemplates)
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

  def setformats(self, formats, usetemplates):
    """sets the input formats to the given list/single string"""
    inputformats = []
    outputformats = []
    templateformats = []
    self.outputoptions = {}
    self.usetemplates = usetemplates
    for formatgroup, outputoptions in formats.iteritems():
      if isinstance(formatgroup, (str, unicode)):
        formatgroup = (formatgroup, )
      if not isinstance(formatgroup, tuple):
        raise ValueError("formatgroups must be tuples or str/unicode")
      if len(formatgroup) < 1 or len(formatgroup) > 2:
        raise ValueError("formatgroups must be tuples of length 1 or 2")
      if len(formatgroup) == 1:
        formatgroup += (None, )
      inputformat, templateformat = formatgroup
      if not isinstance(outputoptions, tuple) or len(outputoptions) != 2:
        raise ValueError("output options must be tuples of length 2")
      outputformat, converter = outputoptions
      if not inputformat in inputformats: inputformats.append(inputformat)
      if not outputformat in outputformats: outputformats.append(outputformat)
      if not templateformat in templateformats: templateformats.append(templateformat)
      self.outputoptions[(inputformat, templateformat)] = (outputformat, converter)
    self.inputformats = inputformats
    inputformathelp = self.getformathelp(inputformats)
    inputoption = optparse.Option("-i", "--input", dest="input", default=None, metavar="INPUT",
                    help="read from INPUT in %s" % (inputformathelp))
    inputoption.optionalswitch = True
    inputoption.required = True
    self.define_option(inputoption)
    outputformathelp = self.getformathelp(outputformats)
    outputoption = optparse.Option("-o", "--output", dest="output", default=None, metavar="OUTPUT",
                    help="write to OUTPUT in %s" % (outputformathelp))
    outputoption.optionalswitch = True
    outputoption.required = True
    self.define_option(outputoption)
    if self.usetemplates:
      self.templateformats = templateformats
      templateformathelp = self.getformathelp(self.templateformats)
      templateoption = optparse.Option("-t", "--template", dest="template", default=None, metavar="TEMPLATE",
                  help="read from TEMPLATE in %s" % (templateformathelp))
      self.define_option(templateoption)

  def setprogressoptions(self):
    """sets the progress options"""
    self.progresstypes = {"none": progressbar.NoProgressBar, "simple": progressbar.SimpleProgressBar,
                          "console": progressbar.ConsoleProgressBar, "verbose": progressbar.VerboseProgressBar}
    progressoption = optparse.Option(None, "--progress", dest="progress", default="console",
                      choices = self.progresstypes.keys(), metavar="PROGRESS",
                      help="set progress type to one of %s" % (", ".join(self.progresstypes)))
    self.define_option(progressoption)

  def setpotoption(self):
    """sets the -P/--pot option depending on input/output formats etc"""
    if self.usepots:
      potoption = optparse.Option("-P", "--pot", action="store_true", dest="pot", default=False, \
                                 help="use PO template files (.pot) rather than PO files (.po)")
      self.define_option(potoption)

  def getformathelp(self, formats):
    """make a nice help string for describing formats..."""
    if self.usepots and "po" in formats:
      if isinstance(formats, dict):
        formats["pot"] = formats["po"]
      else:
        formats.append("pot")
    formats = [format for format in formats if format is not None]
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

  def getoutputoptions(self, inputpath, templatepath):
    """works out which conversion method to use..."""
    if inputpath:
      inputbase, inputext = os.path.splitext(inputpath)
      inputext = inputext.replace(os.extsep, "", 1)
    else:
      inputext = None
    if templatepath:
      templatebase, templateext = os.path.splitext(templatepath)
      templateext = templateext.replace(os.extsep, "", 1)
    else:
      templateext = None
    if (inputext, templateext) in self.outputoptions:
      return self.outputoptions[inputext, templateext]
    elif (inputext, None) in self.outputoptions:
      return self.outputoptions[inputext, None]
    elif (None, templateext) in self.outputoptions:
      return self.outputoptions[None, templateext]
    else:
      raise ValueError("could not find outputoptions for inputext %s, templateext %s" % (inputext, templateext))

  def initprogressbar(self, allfiles, options):
    """sets up a progress bar appropriate to the options and files"""
    if options.progress in ('console', 'verbose'):
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
      else:
        allfiles = [options.input]
    options.recursiveoutput = self.isrecursive(options.output)
    options.recursivetemplate = self.usetemplates and self.isrecursive(options.template)
    allfiles = self.initprogressbar(allfiles, options)
    for inputpath in allfiles:
      templatepath = self.gettemplatename(options, inputpath)
      outputformat, convertmethod = self.getoutputoptions(inputpath, templatepath)
      fullinputpath = self.getfullinputpath(options, inputpath)
      fulltemplatepath = self.getfulltemplatepath(options, templatepath)
      outputpath = self.getoutputname(options, inputpath, outputformat)
      fulloutputpath = self.getfulloutputpath(options, outputpath)
      if options.recursiveoutput and outputpath:
        self.checksubdir(options.output, os.path.dirname(outputpath))
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

  def templateexists(self, options, templatepath):
    """returns whether the given template exists..."""
    fulltemplatepath = self.getfulltemplatepath(options, templatepath)
    return os.path.isfile(fulltemplatepath)

  def gettemplatename(self, options, inputname):
    """gets an output filename based on the input filename"""
    inputbase, inputext = os.path.splitext(inputname)
    inputext = inputext.replace(os.extsep, "", 1)
    if self.usetemplates and options.template:
      for inputext1, templateext1 in self.outputoptions:
        if inputext == inputext1:
          if templateext1:
            templatepath = inputbase + os.extsep + templateext1
            if self.templateexists(options, templatepath):
              return templatepath
    return None

  def getoutputname(self, options, inputname, outputformat):
    """gets an output filename based on the input filename"""
    if not inputname or not options.recursiveoutput: return options.output
    inputbase, inputext = os.path.splitext(inputname)
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

