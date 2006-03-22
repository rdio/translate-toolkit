#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

"""converts gettext .pot template to .po translation files, merging in existing translations if present"""

from translate.storage import po

def convertpot(inputfile, outputfile, templatefile):
  """reads in inputfile pot, adjusts header, writes to outputfile. if templatefile exists, merge translations from it"""
  inputpo = po.pofile(inputfile)
  outputpo = po.pofile()
  # header values
  charset = "UTF-8"
  encoding = "8bit"
  project_id_version = None
  pot_creation_date = None
  po_revision_date = True
  last_translator = None
  language_team = None
  mimeversion = None
  kwargs = {}
  if templatefile is not None:
    templatepo = po.pofile(templatefile)
    templatepo.makeindex()
    templateheadervalues = templatepo.parseheader()
    for key, value in templateheadervalues.iteritems():
      if key == "Project-Id-Version":
        project_id_version = value
      elif key == "Last-Translator":
        last_translator = value
      elif key == "Language-Team":
        language_team = value
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
      project_id_version = value
    elif key in ("Last-Translator", "Language-Team", "PO-Revision-Date", "Content-Type", "Content-Transfer-Encoding"):
      # don't know how to handle these keys, or ignoring them
      pass
    elif key == "POT-Creation-Date":
      pot_creation_date = value
    elif key == "MIME-Version":
      mimeversion = value
    else:
      kwargs[key] = value
  outputheaderpo = outputpo.makeheader(charset=charset, encoding=encoding, project_id_version=project_id_version,
    pot_creation_date=pot_creation_date, po_revision_date=po_revision_date, last_translator=last_translator,
    language_team=language_team, **kwargs)
  outputpo.units.append(outputheaderpo)
  for thepo in inputpo.units:
    if not thepo.isheader():
      if templatefile:
        possiblematches = []
        for source in thepo.getids():
          otherpo = templatepo.sourceindex.get(source, None)
          if otherpo is not None:
            possiblematches.append(otherpo)
        if len(thepo.getids()) == 0:
          otherpo = templatepo.findunit(thepo.source)
        if otherpo:
          possiblematches.append(otherpo)
        for otherpo in possiblematches:
          # TODO: do fuzzy merging if not entirely matching
          if po.unquotefrompo(thepo.msgid, joinwithlinebreak=False) == po.unquotefrompo(otherpo.msgid, joinwithlinebreak=False):
            thepo.merge(otherpo)
            break
        outputpo.units.append(thepo)
      else:
        outputpo.units.append(thepo)
  outputfile.write(str(outputpo))
  return 1

def main(argv=None):
  from translate.convert import convert
  formats = {"pot": ("po", convertpot), ("pot", "po"): ("po", convertpot)}
  parser = convert.ConvertOptionParser(formats, usepots=True, usetemplates=True, description=__doc__)
  parser.run(argv)

