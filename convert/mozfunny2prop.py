#!/usr/bin/env python

"""converts funny mozilla files to properties files"""

import sys
import string

lines = sys.stdin.readlines()

hashstarts = len([line for line in lines if line.startswith("#")])
if hashstarts:
  # this is a .inc file with #defines in it
  sys.stdout.write("# converted from #defines file\n")
  for line in lines:
    if not line.strip():
      sys.stdout.write(line)
    elif line.startswith("#define"):
      parts = string.split(line.replace("#define", "", 1).strip(), maxsplit=1)
      if not parts:
        continue
      if len(parts) == 1:
        key, value = parts[0], ""
      else:
        key, value = parts
      sys.stdout.write("%s = %s\n" % (key, value))
    else:
      sys.stdout.write(line)
else:
  # this is a pseudo-properties .it file
  sys.stdout.write("# converted from pseudo-properties .it file\n")
  for line in lines:
    if not line.strip():
      sys.stdout.write(line)
    elif line.lstrip().startswith(";"):
      sys.stdout.write(line.replace(";", "#", 1))
    elif line.lstrip().startswith("[") and line.rstrip().endswith("]"):
      sys.stdout.write("# section: "+line)
    else:
      sys.stdout.write(line)

