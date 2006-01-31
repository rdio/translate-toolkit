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

"""classes that hold units of comma-separated values (.csv) files (csvunit)
or entire files (csvfile) for use with localisation
"""

try:
  # try to import the standard csv module, included from Python 2.3
  import csv
except:
  # if it doesn't work, use our local copy of it...
  from translate.misc import csv

from translate.misc import sparse
from translate.storage import base

class SimpleDictReader:
  def __init__(self, fileobj, fieldnames):
    self.fieldnames = fieldnames
    self.contents = fileobj.read()
    self.parser = sparse.SimpleParser(defaulttokenlist=[",", "\n"],whitespacechars="\r")
    self.parser.stringescaping = 0
    self.parser.quotechars = '"'
    self.tokens = self.parser.tokenize(self.contents)
    self.tokenpos = 0

  def __iter__(self):
    return self

  def getvalue(self, value):
    """returns a value, evaluating strings as neccessary"""
    if (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
      return sparse.stringeval(value).replace("\r","").replace("\n","")
    else:
      return value

  def next(self):
    while self.tokenpos < len(self.tokens) and self.tokens[self.tokenpos] == "\n":
      self.tokenpos += 1
    if self.tokenpos >= len(self.tokens):
      raise StopIteration()
    thistokens = []
    while self.tokenpos < len(self.tokens) and self.tokens[self.tokenpos] != "\n":
      thistokens.append(self.tokens[self.tokenpos])
      self.tokenpos += 1
    while self.tokenpos < len(self.tokens) and self.tokens[self.tokenpos] == "\n":
      self.tokenpos += 1
    fields = []
    # patch together fields since we can have quotes inside a field
    currentfield = ''
    fieldparts = 0
    for token in thistokens:
      if token == ',':
        # a field is only quoted if the whole thing is quoted
        if fieldparts == 1:
          currentfield = self.getvalue(currentfield)
        fields.append(currentfield)
        currentfield = ''
        fieldparts = 0
      else:
        currentfield += token
        fieldparts += 1
    # things after the last comma...
    if fieldparts:
      if fieldparts == 1:
        currentfield = self.getvalue(currentfield)
      fields.append(currentfield)
    values = {}
    for fieldnum in range(len(self.fieldnames)):
      if fieldnum >= len(fields):
        values[self.fieldnames[fieldnum]] = ""
      else:
        values[self.fieldnames[fieldnum]] = fields[fieldnum]
    return values

class csvunit(base.TranslationUnit):
  def __init__(self, source=None):
    self.sourcecomment = ""
    self.msgid = source
    self.msgstr = ""

  def getsource(self):
    return self.msgid

  def setsource(self, source):
    self.msgid = source
  source = property(getsource, setsource)

  def gettarget(self):
    return self.msgstr

  def settarget(self, target):
    self.msgstr = target
  target = property(gettarget, settarget)

  def fromdict(self, cedict):
    self.sourcecomment = cedict.get('source', '')
    self.msgid = cedict.get('msgid', '')
    self.msgstr = cedict.get('msgstr', '')
    if self.sourcecomment is None: self.sourcecomment = ''
    if self.msgid is None: self.msgid = ''
    if self.msgstr is None: self.msgstr = ''
    if self.msgid[:2] in ("\\+", "\\-"): self.msgid = self.msgid[1:]
    if self.msgstr[:2] in ("\\+", "\\-"): self.msgstr = self.msgstr[1:]

  def todict(self, encoding='utf-8'):
    sourcecomment, msgid, msgstr = self.sourcecomment, self.msgid, self.msgstr
    if isinstance(sourcecomment, unicode):
      sourcecomment = sourcecomment.encode(encoding)
    if isinstance(msgid, unicode):
      msgid = msgid.encode(encoding)
    if isinstance(msgstr, unicode):
      msgstr = msgstr.encode(encoding)
    return {'source':sourcecomment, 'msgid': msgid, 'msgstr': msgstr}

class csvfile(base.TranslationStore):
  """This class represents a .csv file with various lines. 
  The default format contains three columns: comments, source, target"""
  UnitClass = csvunit
  def __init__(self, inputfile=None, fieldnames=None):
    self.units= []
    if fieldnames is None:
      self.fieldnames = ['source', 'msgid', 'msgstr']
    else:
      if isinstance(fieldnames, basestring):
        fieldnames = [fieldname.strip() for fieldname in fieldnames.split(",")]
      self.fieldnames = fieldnames
    self.filename = getattr(inputfile, 'name', '')
    if inputfile is not None:
      csvsrc = inputfile.read()
      inputfile.close()
      self.parse(csvsrc)

  def parse(self, csvsrc):
    csvfile = csv.StringIO(csvsrc)
    reader = SimpleDictReader(csvfile, self.fieldnames)
    for row in reader:
      newce = self.UnitClass()
      newce.fromdict(row)
      self.units.append(newce)

  def __str__(self):
    csvfile = csv.StringIO()
    writer = csv.DictWriter(csvfile, self.fieldnames)
    for ce in self.units:
      cedict = ce.todict()
      writer.writerow(cedict)
    csvfile.reset()
    return "".join(csvfile.readlines())

  def parsestring(cls, storestring):
    """Parses the csv file contents in the storestring"""
    parsedfile = csvfile()
    parsedfile.parse(storestring)
    return parsedfile
  parsestring = classmethod(parsestring)


if __name__ == '__main__':
  import sys
  cf = csvfile()
  cf.parse(sys.stdin.read())
  sys.stdout.write(str(cf))

