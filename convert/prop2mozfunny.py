#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""converts properties files back to funny mozilla files"""

import string
from translate.storage import properties
from translate.convert import po2prop
from translate.convert import mozfunny2prop
from translate.misc import quote
from translate.misc.wStringIO import StringIO

def prop2inc(pf):
  """convert a properties file back to a .inc file with #defines in it"""
  # any leftover blanks will not be included at the end
  pendingblanks = []
  for pe in pf.propelements:
    for comment in pe.comments:
      if comment.startswith("# converted from") and "#defines" in comment:
        pass
      else:
        for blank in pendingblanks:
          yield blank
        # TODO: could convert commented # x=y back to # #define x y
        yield comment
    if pe.isblank():
      pendingblanks.append("\n")
    else:
      definition = "#define %s %s\n" % (pe.name, pe.msgid.replace("\n", "\\n"))
      if isinstance(definition, unicode):
        definition = definition.encode("UTF-8")
      for blank in pendingblanks:
        yield blank
      yield definition

def prop2it(pf):
  """convert a properties file back to a pseudo-properties .it file"""
  for pe in pf.propelements:
    for comment in pe.comments:
      if comment.startswith("# converted from") and "pseudo-properties" in comment:
        pass
      elif comment.startswith("# section: "):
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

def prop2funny(src, itencoding="cp1252"):
  lines = src.split("\n")
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
  pf.parse("\n".join(lines))
  if wasdefines:
    for line in prop2inc(pf):
      yield line + "\n"
  elif waspseudoprops:
    for line in prop2it(pf):
      yield line.decode("utf-8").encode(itencoding) + "\n"

def po2inc(inputfile, outputfile, templatefile, encoding=None, includefuzzy=False):
  """wraps po2prop but converts outputfile to properties first"""
  outputpropfile = StringIO()
  if templatefile is not None:
    templatelines = templatefile.readlines()
    templateproplines = [mozfunny2prop.encodepropline(line) for line in mozfunny2prop.inc2prop(templatelines)]
    templatepropfile = StringIO("".join(templateproplines))
  else:
    templatepropfile = None
  result = po2prop.convertprop(inputfile, outputpropfile, templatepropfile, includefuzzy=includefuzzy)
  if result:
    outputpropfile.seek(0)
    pf = properties.propfile(outputpropfile)
    outputlines = prop2inc(pf)
    outputfile.writelines(outputlines)
  return result

def po2it(inputfile, outputfile, templatefile, encoding="cp1252", includefuzzy=False):
  """wraps po2prop but converts outputfile to properties first"""
  outputpropfile = StringIO()
  if templatefile is not None:
    templatelines = templatefile.readlines()
    templateproplines = [mozfunny2prop.encodepropline(line) for line in mozfunny2prop.it2prop(templatelines, encoding=encoding)]
    templatepropfile = StringIO("".join(templateproplines))
  else:
    templatepropfile = None
  result = po2prop.convertprop(inputfile, outputpropfile, templatepropfile, includefuzzy=includefuzzy)
  if result:
    outputpropfile.seek(0)
    pf = properties.propfile(outputpropfile)
    outputlines = prop2it(pf)
    for line in outputlines:
      line = line.decode("utf-8").encode(encoding)
      outputfile.write(line)
  return result

def po2ini(inputfile, outputfile, templatefile, encoding="UTF-8", includefuzzy=False):
  """wraps po2prop but converts outputfile to properties first using UTF-8 encoding"""
  return po2it(inputfile=inputfile, outputfile=outputfile, templatefile=templatefile, encoding=encoding, includefuzzy=includefuzzy)

def main(argv=None):
  import sys
  # TODO: get encoding from charset.mk, using parameter
  src = sys.stdin.read()
  for line in prop2funny(src):
    sys.stdout.write(line)

if __name__ == "__main__":
  main()

