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

try:
  import optparse
except ImportError:
  from translate.misc import optparse
from translate import __version__

norecursion = 0
optionalrecursion = 1
defaultrecursion = 2

class ConvertOptionParser(optparse.OptionParser, object):
  """a specialized Option Parser for convertor tools..."""
  def __init__(self, recursive, inputformats, outputformats, usetemplates):
    """construct the specialized Option Parser"""
    super(ConvertOptionParser, self).__init__(version="%prog "+__version__.ver)
    usage = "%prog [options] "
    if recursive == defaultrecursion:
      argumentdesc = "dir"
    elif recursive == optionalrecursion:
      self.add_option("-R", "--recursive", action="store_true", dest="recursive", default=False, \
        help="recurse subdirectories")
      argumentdesc = "file/dir"
    elif not recursive:
      argumentdesc = "file"
    else:
      raise ValueError("invalid recursive argument: %r" % recursive)
    if isinstance(inputformats, basestring):
      inputformats = [inputformats]
      inputformathelp = "%s format" % inputformats
    else:
      inputformathelp = ", ".join(inputformats) + " formats"
    if isinstance(outputformats, basestring):
      outputformats = [outputformats]
      outputformathelp = "%s format" % outputformats
    else:
      outputformathelp = ", ".join(outputformats) + " formats"
    self.add_option("-i", "--input", dest="input", default=None, metavar="INPUT",
                    help="read from INPUT %s in %s" % (argumentdesc, inputformathelp))
    usage += "[-i|--input INPUT] " 
    self.add_option("-o", "--output", dest="output", default=None, metavar="OUTPUT",
                    help="write to OUTPUT %s in %s" % (argumentdesc, outputformathelp))
    usage += "[-o|--output OUTPUT] " 
    if usetemplates:
      self.add_option("-t", "--template", dest="template", default=None, metavar="TEMPLATE",
                    help="read from TEMPLATE %s in %s" % (argumentdesc, inputformathelp))
      usage += "[-t|--template TEMPLATE] "
    self.set_usage(usage.strip())

