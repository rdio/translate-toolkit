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

"""simple parser / string tokenizer"""

# the approach is: rather than returning a list of token types etc,
# we simple return a list of tokens...

def stringeval(input):
  """takes away repeated quotes (escapes) and returns the string represented by the input"""
  stringchar = input[0]
  if input[-1] != stringchar or stringchar not in ("'",'"'):
    # scratch your head
    raise ValueError, "error parsing escaped string"
  return input[1:-1].replace(stringchar+stringchar,stringchar)

class stringstring(str):
  """this is used to intelligently keep track of strings that are actually quoted strings, internally"""
  def __init__(self, s):
    self.s = s

def destringstring(str1):
  return getattr(str1, 's', str1)

def stringtokenize(input):
  """makes strings in input into tokens..."""
  tokens = []
  laststart = 0
  instring = 0
  stringchar = ''
  gotclose = 0
  for pos in range(len(input)):
    char = input[pos]
    if instring:
      if char == stringchar:
        gotclose = not gotclose
      elif gotclose:
        tokens.append(input[laststart:pos])
        instring, laststart, stringchar = 0, pos, ''
    if not instring:
      if char in ("'",'"'):
        if pos > laststart: tokens.append(input[laststart:pos])
        instring, laststart, stringchar, gotclose = 1, pos, char, 0
  if laststart < len(input): tokens.append(input[laststart:])
  return [stringstring(token) for token in tokens]

defaulttokenlist = ['<=', '>=', '==', '!=', '+=', '-=', '*=', '/=', '<>']
defaulttokenlist.extend('(),[]:=+-')

def separatetokens(input, tokenlist = defaulttokenlist):
  """this separates out tokens in tokenlist from whitespace etc"""
  # don't retokenize strings
  if type(input) == stringstring and input[0] in ("'",'"'): return [input]
  # loop through and put tokens into a list
  tokens = []
  pos = 0
  laststart = 0
  while pos < len(input):
    foundtoken = 0
    for token in tokenlist:
      if input[pos:pos+len(token)] == token:
        if laststart < pos: tokens.append(input[laststart:pos])
        tokens.append(token)
        pos += len(token)
        foundtoken, laststart = 1, pos
        break
    if not foundtoken: pos += 1
  if laststart < len(input): tokens.append(input[laststart:])
  return tokens

def separategiventokensfn(tokenlist):
  def separategiventokens(input):
    """this separates out the given tokens from whitespace etc"""
    return separatetokens(input, tokenlist)
  return separategiventokens

def removewhitespace(input, whitespacechars=" \t\r\n", includewhitespacetokens=0):
  """this removes whitespace but lets it separate things out into separate tokens"""
  # don't retokenize strings
  if type(input) == stringstring and input[0] in ("'",'"'): return [input]
  # loop through and put tokens into a list
  tokens = []
  pos = 0
  inwhitespace = 0
  laststart = 0
  for pos in range(len(input)):
    char = input[pos]
    if inwhitespace:
      if char not in whitespacechars:
        if laststart < pos and includewhitespacetokens: tokens.append(input[laststart:pos])
        inwhitespace, laststart = 0, pos
    else:
      if char in whitespacechars:
        if laststart < pos: tokens.append(input[laststart:pos])
        inwhitespace, laststart = 1, pos
  if laststart < len(input) and (not inwhitespace or includewhitespacetokens):
    tokens.append(input[laststart:])
  return tokens

def applytokenizer(inputlist, tokenizer, destringstringthem=1):
  """apply a tokenizer to a set of input, flattening the result"""
  tokenizedlists = [tokenizer(inputstr) for inputstr in inputlist]
  joined = []
  map(joined.extend, tokenizedlists)
  if destringstringthem:
    return [destringstring(token) for token in joined]
  return joined

def applytokenizers(inputlist, tokenizers, destringstringthem=1):
  """apply a set of tokenizers to a set of input, flattening each time"""
  for tokenizer in tokenizers:
    inputlist = applytokenizer(inputlist, tokenizer, 0)
  if destringstringthem:
    return [destringstring(token) for token in inputlist]
  return inputlist

def tokenize(input):
  """tokenize the input string with the standard tokenizers"""
  return applytokenizers([input], [stringtokenize, removewhitespace, separatetokens])
  
def findtokenpos(input, tokens, tokennum):
  """finds the position of the given token in the input"""
  currenttokenpos = 0
  for currenttokennum in range(tokennum+1):
    currenttokenpos = input.find(tokens[currenttokennum], currenttokenpos)
  return currenttokenpos

