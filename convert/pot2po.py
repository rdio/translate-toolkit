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

"""convert a gettext .pot template to a .po translation file, merging in existing translations if present"""

from translate.storage import po

def convertpot(inputfile, outputfile, templatefile):
  """reads in inputfile pot, adjusts header, writes to outputfile. if templatefile exists, merge translations from it"""
  inputpo = po.pofile(inputfile)
  outputpo = po.pofile()
  # header values
  charset = "UTF-8"
  encoding = "8bit"
  projectid = None
  creationdate = None
  revisiondate = True
  lasttranslator = None
  languageteam = None
  mimeversion = None
  kwargs = {}
  if templatefile is not None:
    templatepo = po.pofile(templatefile)
    templatepo.makeindex()
    templateheadervalues = templatepo.parseheader()
    for key, value in templateheadervalues.iteritems():
      if key == "Project-Id-Version":
        projectid = value
      elif key == "Last-Translator":
        lasttranslator = value
      elif key == "Language-Team":
        languageteam = value
      elif key in ("POT-Creation-Date", "PO-Revision-Date", "MIME-Version"):
        # don't know how to handle these keys, or ignoring them
        pass
      elif key == "Content-Type":
        kwargs[key] = value
      elif key == "Content-Transfer-Encoding":
        encoding = value
      else:
        kwargs[key] = value
  inputheadervalues = inputpo.parseheader()
  for key, value in inputheadervalues.iteritems():
    if key == "Project-Id-Version":
      projectid = value
    elif key in ("Last-Translator", "Language-Team", "PO-Revision-Date", "Content-Type", "Content-Transfer-Encoding"):
      # don't know how to handle these keys, or ignoring them
      pass
    elif key == "POT-Creation-Date":
      creationdate = value
    elif key == "MIME-Version":
      mimeversion = value
    else:
      kwargs[key] = value
  outputheaderpo = outputpo.makeheader(charset=charset, encoding=encoding, projectid=projectid,
    creationdate=creationdate, revisiondate=revisiondate, lasttranslator=lasttranslator,
    languageteam=languageteam, **kwargs)
  outputpo.poelements.append(outputheaderpo)
  for thepo in inputpo.poelements:
    if not thepo.isheader():
      if templatefile:
        possiblematches = []
        for source in thepo.getsources():
          otherpo = templatepo.sourceindex.get(source, None)
          if otherpo is not None:
            possiblematches.append(otherpo)
        for otherpo in possiblematches:
          # TODO: do fuzzy merging if not entirely matching
          if po.getunquotedstr(thepo.msgid) == po.getunquotedstr(otherpo.msgid):
            thepo.merge(otherpo)
            break
        outputpo.poelements.append(thepo)
      else:
        outputpo.poelements.append(thepo)
  outputfile.writelines(outputpo.tolines())
  return 1

def main():
  from translate.convert import convert
  formats = {"pot": ("po", convertpot), ("pot", "po"): ("po", convertpot)}
  parser = convert.ConvertOptionParser(formats, usepots=True, usetemplates=True, description=__doc__)
  parser.run()

