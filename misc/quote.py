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

"""string processing utilities for extracting strings with various kinds of delimiters"""

def extract(source,startdelim,enddelim,escape,startinstring=0):
  """Extracts a doublequote-delimited string from a string, allowing for backslash-escaping"""
  # note that this returns the quote characters as well... even internally
  instring = startinstring
  inescape = 0
  # remember where the last start of the string was so we don't look for and end marker before that
  # or alternatively, where the last escape ended. so lastspecial >= laststart
  laststart = 0
  lastspecial = 0
  lenstart = len(startdelim)
  lenend = len(enddelim)
  extracted = ""
  if escape is None: escape = "&&&&&&&&&&&&&&&NOESCAPE&&&&&&&&&&&&&&&&&&" 
  for pos in range(len(source)):
    c = source[pos]
    if instring and inescape:
      # if in an escape, just add to the string
      extracted += c
      lastspecial = pos+1
    elif instring and ((pos-lenend < lastspecial) or (source.find(enddelim,pos-lenend) <> pos-lenend)):
      # if we're in the string and we're not at the end, add to the string
      extracted += c
    else:
      if instring and (pos-lenend >= lastspecial) and (source.find(enddelim,pos-lenend) == pos-lenend) and (not inescape):
        # if we're in the string and we find we've just passed the end, mark that we're out
        instring = not instring
      if (not instring) and (source.find(startdelim,pos) == pos) and (not inescape):
        # if we're not in the string and we find the start, add to the string and mark that we're in
        instring = not instring
        laststart = pos + lenstart
        lastspecial = laststart
        extracted += c
    if (source.find(escape,pos) == pos) and (not inescape):
      inescape = 1
    else:
      inescape = 0
  # if we're right at the end, just check if we've just had an end...
  pos = len(source)
  if instring and (pos-lenend >= laststart) and (source.find(enddelim,pos-lenend) == pos-lenend) and (not inescape):
    instring = not instring
  return (extracted,instring)

def extractfromlines(lines,startdelim,enddelim,escape):
  """Calls extract over multiple lines, remembering whether in the string or not"""
  result = ""
  instring = 0
  for line in lines:
    (string,instring) = extract(line,startdelim,enddelim,escape,instring)
    result += string
    if not instring: break
  return result

def extractstr(source):
  "Extracts a doublequote-delimited string from a string, allowing for backslash-escaping"
  (string,instring) = extract(source,'"','"','\\')
  return string

def extractcomment(lines):
  "Extracts <!-- > XML comments from lines"
  return extractfromlines(lines,"<!--","-->",None)

def extractwithoutquotes(source,startdelim,enddelim,escape,startinstring=0,includeescapes=1):
  """Extracts a doublequote-delimited string from a string, allowing for backslash-escaping
  includeescapes can also be a function that takes the whole escaped string and returns whether to escape it"""
  # note that this doesn't returns the quote characters as well...
  instring = startinstring
  inescape = 0
  # remember where the last start of the string was so we don't look for and end marker before that
  # or alternatively, where the last escape ended. so lastspecial >= laststart
  laststart = 0
  lastspecial = 0
  lenstart = len(startdelim)
  lenend = len(enddelim)
  laststartinextracted = None
  extracted = ""
  for pos in range(len(source)):
    c = source[pos]
    if instring and inescape:
      # if not including escapes in result, take them out
      if callable(includeescapes):
        includethisescape = includeescapes(source[pos-len(escape):pos+1])
      else:
        includethisescape = includeescapes
      if not includethisescape:
        extracted = extracted[:-len(escape)]
      # if in an escape, just add to the string
      extracted += c
      lastspecial = pos+1
    elif instring and ((pos-lenend < lastspecial) or (source.find(enddelim,pos-lenend) <> pos-lenend)):
      # if we're in the string and we're not at the end, add to the string
      extracted += c
    else:
      if instring and (pos-lenend >= lastspecial) and (source.find(enddelim,pos-lenend) == pos-lenend) and (not inescape):
        # if we're in the string and we find we've just passed the end, mark that we're out
        instring = not instring
        # remove the last start bit in the result string and forget it
        if laststartinextracted is not None:
          extracted = extracted[:laststartinextracted] + extracted[laststartinextracted+lenstart:]
        laststartinextracted = None
        # remove the end bit of the string
        extracted = extracted[:-lenend]
      if (not instring) and (source.find(startdelim,pos) == pos) and (not inescape):
        # if we're not in the string and we find the start, add to the string and mark that we're in
        instring = not instring
        laststart = pos + lenstart
        lastspecial = laststart
        laststartinextracted = len(extracted)
        extracted += c
    if escape is not None and (source.find(escape,pos) == pos) and (not inescape):
      inescape = 1
    else:
      inescape = 0

  # take out any remaining start in the resultstring
  if laststartinextracted is not None:
    extracted = extracted[:laststartinextracted] + extracted[laststartinextracted+lenstart:]

  # if we're right at the end, just check if we've just had an end...
  pos = len(source)
  if instring and (pos-lenend >= laststart) and (source.find(enddelim,pos-lenend) == pos-lenend) and (not inescape):
    instring = not instring
    # and remember to remove it
    extracted = extracted[:-lenend]

  return (extracted,instring)

def escapequotes(source, escapeescapes=0):
  "Returns the same string, with double quotes escaped with backslash"
  if escapeescapes:
    return source.replace('\\', '\\\\').replace('"', '\\"')
  else:
    return source.replace('"','\\"')

def escapesinglequotes(source):
  "Returns the same string, with single quotes doubled"
  return source.replace("'","''")

def mozillapropertiesencode(source):
  """encodes source in the escaped-unicode encoding used by mozilla .properties files"""
  output = ""
  for char in source:
    charnum = ord(char)
    if 0 <= charnum < 128:
      output += str(char)
    else:
      output += "\\u%04X" % charnum
  return output

propertyescapes = {
  # escapes that are self-escaping
  "\\": "\\", "'": "'", '"': '"',
  # control characters that we keep
  "b": "\b", "f": "\f", "t": "\t", "n": "\n", "v": "\v", "a": "\a"
  }

controlchars = {
  # the reverse of the above...
  "\b": "\\b", "\f": "\\f", "\t": "\\t", "\n": "\\n", "\v": "\\v"
  }

def escapecontrols(source):
  """escape control characters in the given string"""
  for key, value in controlchars.iteritems():
    source = source.replace(key, value)
  return source

def mozillapropertiesdecode(source):
  """decodes source from the escaped-unicode encoding used by mozilla .properties files"""
  # since the .decode("unicode-escape") routine decodes everything, and we don't want to
  # we reimplemented the algorithm from Python Objects/unicode.c in Python here
  # and modified it to retain escaped control characters
  output = u""
  s = 0
  if isinstance(source, str):
    source = source.decode("utf-8")
  def unichr2(i):
    """Returns a Unicode string of one character with ordinal 32 <= i, otherwise an escaped control character"""
    if 32 <= i:
      return unichr(i)
    elif unichr(i) in controlchars:
      # we just return the character, unescaped
      # if people want to escape them they can use escapecontrols
      return unichr(i)
    else:
      return "\\u%04x" % i
  while s < len(source):
    c = source[s]
    if c != '\\':
      output += c
      s += 1
      continue
    s += 1
    if s >= len(source):
      # this is an escape at the end of the line, which implies a continuation...
      # return the escape to inform the parser
      output += c
      continue
    c = source[s]
    s += 1
    if c == '\n': pass
    # propertyescapes lookups
    elif c in propertyescapes: output += propertyescapes[c]
    # \uXXXX escapes
    # \UXXXX escapes
    elif c in "uU":
      digits = 4
      x = 0
      for digit in range(digits):
        x <<= 4
        if s + digit >= len(source):
          digits = digit
          break
        c = source[s+digit].lower()
        if c.isdigit():
          x += ord(c) - ord('0')
        elif c in "abcdef":
          x += ord(c) - ord('a') + 10
        else:
          break
      s += digits
      output += unichr2(x)
    elif c == "N":
      if source[s] != "{":
        raise ValueError("Invalid named unicode escape")
      s += 1
      e = source.find("}", s)
      if e == -1:
        raise ValueError("Invalid named unicode escape")
      import unicodedata
      name = source[s:e]
      output += unicodedata.lookup(name)
      s = e + 1
    else:
      output += "\\" + c
  return output

def quotestr(source, escapeescapes=0):
  "Returns a doublequote-delimited quoted string, escaping double quotes with backslash"
  if isinstance(source, list):
    firstline = True
    for line in source:
      if firstline:
        newsource = '"' + escapequotes(line, escapeescapes) + '"'     
        firstline = False
      else:
        newsource = newsource + '\n' + '"' + escapequotes(line, escapeescapes) + '"'
    return newsource
  else:
    return '"' + escapequotes(source, escapeescapes) + '"'

def singlequotestr(source):
  "Returns a doublequote-delimited quoted string, escaping single quotes with themselves"
  return "'" + escapesinglequotes(source) + "'"

def eitherquotestr(source):
  "Returns a singlequote- or doublequote-delimited string, depending on what quotes it contains"
  if '"' in source:
    return singlequotestr(source)
  else:
    return quotestr(source)

def findend(string,substring):
  s = string.find(substring)
  if s <> -1:
    s += len(substring)
  return s

def rstripeol(string):
  e = len(string)
  while (e > 0) and (string[e-1] in ['\n','\r']): e -= 1
  return string[:e]

def stripcomment(comment,startstring="<!--",endstring="-->"):
  cstart = comment.find(startstring)
  if cstart == -1:
    cstart = 0
  else:
    cstart += len(startstring)
  cend = comment.find(endstring,cstart)
  return comment[cstart:cend].strip()

def unstripcomment(comment,startstring="<!-- ",endstring=" -->\n"):
  return startstring+comment.strip()+endstring

def encodewithdict(unencoded, encodedict):
  """encodes certain characters in the string using an encode dictionary"""
  encoded = unencoded
  for key, value in encodedict.iteritems():
    if key in encoded:
      encoded = encoded.replace(key, value)
  return encoded

def makeutf8(d):
  """convert numbers to utf8 codes in the values of a dictionary"""
  for key, value in d.items():
    if type(value) == int:
      d[key] = unichr(value).encode('utf8')
  return d

def testcase():
  x = ' "this" " is " "a" " test!" '
  print extract(x,'"','"',None)
  print extract(x,'"','"','!')
  print extractwithoutquotes(x,'"','"',None)
  print extractwithoutquotes(x,'"','"','!')
  print extractwithoutquotes(x,'"','"','!',includeescapes=0)

if __name__ == '__main__':
  testcase()

