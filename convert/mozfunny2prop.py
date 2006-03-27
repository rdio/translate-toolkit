#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""converts funny mozilla files to properties files"""

import string
from translate.misc import quote
from translate.convert import prop2po
from translate.misc.wStringIO import StringIO

def inc2prop(lines):
  """convert a .inc file with #defines in it to a properties file"""
  yield "# converted from #defines file\n"
  for line in lines:
    line = line.decode("utf-8")
    if not line.strip():
      yield line
    elif line.startswith("#define"):
      parts = string.split(line.replace("#define", "", 1).strip(), maxsplit=1)
      if not parts:
        continue
      if len(parts) == 1:
        key, value = parts[0], ""
      else:
        key, value = parts
      yield "%s = %s\n" % (key, value)
    else:
      yield line

def it2prop(lines, encoding="cp1252"):
  """convert a pseudo-properties .it file to a conventional properties file"""
  yield "# converted from pseudo-properties .it file\n"
  # differences: ; instead of # for comments
  #              [section] titles that we replace with # section: comments
  for line in lines:
    line = line.decode(encoding)
    if not line.strip():
      yield line
    elif line.lstrip().startswith(";"):
      yield line.replace(";", "#", 1)
    elif line.lstrip().startswith("[") and line.rstrip().endswith("]"):
      yield "# section: "+line
    else:
      yield line

def funny2prop(lines, itencoding="cp1252"):
  hashstarts = len([line for line in lines if line.startswith("#")])
  if hashstarts:
    for line in inc2prop(lines):
      yield quote.mozillapropertiesencode(line)
  else:
    for line in it2prop(lines, encoding=itencoding):
      yield quote.mozillapropertiesencode(line)

def inc2po(inputfile, outputfile, templatefile, encoding=None, pot=False, duplicatestyle="msgid_comment"):
  """wraps prop2po but converts input/template files to properties first"""
  inputlines = inputfile.readlines()
  inputproplines = [quote.mozillapropertiesencode(line) for line in inc2prop(inputlines)]
  inputpropfile = StringIO("".join(inputproplines))
  if templatefile is not None:
    templatelines = templatefile.readlines()
    templateproplines = [quote.mozillapropertiesencode(line) for line in inc2prop(templatelines)]
    templatepropfile = StringIO("".join(templateproplines))
  else:
    templatepropfile = None
  return prop2po.convertprop(inputpropfile, outputfile, templatepropfile, pot=pot, duplicatestyle=duplicatestyle)

def it2po(inputfile, outputfile, templatefile, encoding="cp1252", pot=False, duplicatestyle="msgid_comment"):
  """wraps prop2po but converts input/template files to properties first"""
  inputlines = inputfile.readlines()
  inputproplines = [quote.mozillapropertiesencode(line) for line in it2prop(inputlines, encoding=encoding)]
  inputpropfile = StringIO("".join(inputproplines))
  if templatefile is not None:
    templatelines = templatefile.readlines()
    templateproplines = [quote.mozillapropertiesencode(line) for line in it2prop(templatelines, encoding=encoding)]
    templatepropfile = StringIO("".join(templateproplines))
  else:
    templatepropfile = None
  return prop2po.convertprop(inputpropfile, outputfile, templatepropfile, pot=pot, duplicatestyle=duplicatestyle)

def ini2po(inputfile, outputfile, templatefile, encoding="UTF-8", pot=False, duplicatestyle="msgid_comment"):
  return it2po(inputfile=inputfile, outputfile=outputfile, templatefile=templatefile, encoding=encoding, pot=pot, duplicatestyle=duplicatestyle)

def main(argv=None):
  import sys
  lines = sys.stdin.readlines()
  for line in funny2prop(lines):
    sys.stdout.write(line)

if __name__ == "__main__":
  main()

