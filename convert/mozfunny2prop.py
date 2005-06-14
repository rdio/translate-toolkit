#!/usr/bin/env python

"""converts funny mozilla files to properties files"""

import string
from translate.misc import quote

def defines2prop(lines):
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

def it2prop(lines):
  """convert a pseudo-properties .it file to a conventional properties file"""
  yield "# converted from pseudo-properties .it file\n"
  # differences: ; instead of # for comments
  #              [section] titles that we replace with # section: comments
  for line in lines:
    # TODO: get encoding from charset.mk, using parameter
    line = line.decode("cp1252")
    if not line.strip():
      yield line
    elif line.lstrip().startswith(";"):
      yield line.replace(";", "#", 1)
    elif line.lstrip().startswith("[") and line.rstrip().endswith("]"):
      yield "# section: "+line
    else:
      yield line

def funny2prop(lines):
  hashstarts = len([line for line in lines if line.startswith("#")])
  if hashstarts:
    for line in defines2prop(lines):
      yield quote.mozillapropertiesencode(line)
  else:
    for line in it2prop(lines):
      yield quote.mozillapropertiesencode(line)

if __name__ == "__main__":
  import sys
  lines = sys.stdin.readlines()
  for line in funny2prop(lines):
    sys.stdout.write(line)

