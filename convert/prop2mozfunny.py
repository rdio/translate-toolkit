#!/usr/bin/env python

"""converts properties files back to funny mozilla files"""

import sys
import string

lines = sys.stdin.readlines()

header = lines[0]
if not header.startswith("# converted from "):
  waspseudoprops = len([line for line in lines if line.startswith("# section:")])
  wasdefines = len([line for line in lines if line.startswith("#filter") or line.startswith("#unfilter")])
else:
  waspseudoprops = "pseudo-properties" in header
  wasdefines = "#defines" in header
  lines = lines[1:]
if not (waspseudoprops ^ wasdefines):
  print >>sys.stderr, "could not determine file type"
  sys.exit()

from translate.storage import properties
pf = properties.propfile()
pf.fromlines(lines)
if wasdefines:
  # this was a .inc file with #defines in it
  for pe in pf.propelements:
    for comment in pe.comments:
      sys.stdout.write(comment)
    if pe.isblank():
      sys.stdout.write("\n")
    else:
      sys.stdout.write("#define %s %s\n" % (pe.name, pe.msgid.replace("\n", "\\n")))
elif waspseudoprops:
  # this was a pseudo-properties .it file
  for pe in pf.propelements:
    for comment in pe.comments:
      if comment.startswith("# section: "):
        sys.stdout.write(comment.replace("# section: ", "", 1))
      else:
        sys.stdout.write(comment.replace("#", ";", 1))
    if pe.isblank():
      sys.stdout.write("\n")
    else:
      sys.stdout.write("%s=%s\n" % (pe.name, pe.msgid))

