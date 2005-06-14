#!/usr/bin/env python

"""converts properties files back to funny mozilla files"""

from translate.storage import properties
import string

def prop2defines(pf):
  """convert a properties file back to a .inc file with #defines in it"""
  for pe in pf.propelements:
    for comment in pe.comments:
      yield comment
    if pe.isblank():
      yield "\n"
    else:
      definition = "#define %s %s\n" % (pe.name, pe.msgid.replace("\n", "\\n"))
      if isinstance(definition, unicode):
        definition = definition.encode("UTF-8")
      yield definition

def prop2it(pf):
  """convert a properties file back to a pseudo-properties .it file"""
  for pe in pf.propelements:
    for comment in pe.comments:
      if comment.startswith("# section: "):
        yield comment.replace("# section: ", "", 1)
      else:
        yield comment.replace("#", ";", 1)
    if pe.isblank():
      yield "\n"
    else:
      definition = "%s=%s\n" % (pe.name, pe.msgid)
      if isinstance(definition, unicode):
        definition = definition.encode("UTF-8")
      yield definition

def prop2funny(lines, itencoding="cp1252"):
  header = lines[0]
  if not header.startswith("# converted from "):
    waspseudoprops = len([line for line in lines if line.startswith("# section:")])
    wasdefines = len([line for line in lines if line.startswith("#filter") or line.startswith("#unfilter")])
  else:
    waspseudoprops = "pseudo-properties" in header
    wasdefines = "#defines" in header
    lines = lines[1:]
  if not (waspseudoprops ^ wasdefines):
    raise ValueError("could not determine file type as pseudo-properties or defines file")
  pf = properties.propfile()
  pf.fromlines(lines)
  if wasdefines:
    return prop2defines(pf)
  elif waspseudoprops:
    for line in prop2it(pf):
      yield line.decode("utf-8").encode(itencoding)

if __name__ == "__main__":
  import sys
  # TODO: get encoding from charset.mk, using parameter
  lines = sys.stdin.readlines()
  for line in prop2funny(lines):
    sys.stdout.write(line)

