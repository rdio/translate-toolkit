#!/usr/bin/python

"""takes a .po translation file and produces word counts and other statistics"""

import sys
import os
from translate.storage import po
import sre

if not hasattr(__builtins__, "sum"):
  def sum(parts):
    return reduce(int.__add__, parts, 0)

def untranslatedwords(pair):
  original, translation = pair
  if translation.words != 0: return 0
  return original.words

def wordcount(postr):
  # TODO: po class should understand KDE style plurals
  unquotedstr = sre.sub("^_n: ", "", po.getunquotedstr(postr))
  return len(unquotedstr.split())

def wordsinpoel(poel):
  """counts the words in the msgid, msgstr, taking plurals into account"""
  msgidwords = wordcount(poel.msgid)
  if poel.hasplural():
    msgidwords += wordcount(poel.msgid_plural)
  msgstrwords = wordcount(poel.msgstr)
  return msgidwords, msgstrwords

def summarize(elements):
  # ignore totally blank or header elements
  elements = filter(lambda poel: not poel.isheader(), elements)
  translated = filter(lambda poel: not poel.isblankmsgstr() and not poel.isfuzzy(), elements)
  fuzzy = filter(lambda poel: poel.isfuzzy() and not poel.isblankmsgstr(), elements)
  review = filter(lambda poel: poel.isreview(), elements)
  untranslated = filter(lambda poel: poel.isblankmsgstr(), elements)
  wordcounts = dict(map(lambda poel: (poel, wordsinpoel(poel)), elements))
  msgidwords = lambda elementlist: sum(map(lambda poel: wordcounts[poel][0], elementlist))
  msgstrwords = lambda elementlist: sum(map(lambda poel: wordcounts[poel][1], elementlist))
  print "type           strings words (source) words (translation)"
  print "translated:   %5d %10d %15d" % (len(translated), msgidwords(translated), msgstrwords(translated))
  print "fuzzy:        %5d %10d             n/a" % (len(fuzzy), msgidwords(fuzzy))
  print "untranslated: %5d %10d             n/a" % (len(untranslated), msgidwords(untranslated))
  print "Total:        %5d %10d %15d" % (len(translated) + len(fuzzy) + len(untranslated), msgidwords(translated) + msgidwords(fuzzy) + msgidwords(untranslated), msgstrwords(translated))
  if len(review) > 0:
    print "review:       %5d %10d             n/a" % (len(review), msgidwords(review))

class summarizer:
  def __init__(self, filenames):
    self.allelements = []
    self.filecount = 0
    for filename in filenames:
      if not os.path.exists(filename):
        print >>sys.stderr, "cannot process %s: does not exist" % filename
        continue
      elif os.path.isdir(filename):
        self.handledir(filename)
      else:
        self.handlefile(filename)
    if self.filecount > 1:
      print "TOTAL:"
      summarize(self.allelements)
      print "File count:   %5d" % (self.filecount)
      print

  def handlefile(self, filename):
    infile = open(filename)
    pof = po.pofile()
    pof.fromlines(infile.readlines())
    infile.close()
    self.allelements.extend(pof.poelements)
    print filename
    summarize(pof.poelements)
    print
    self.filecount += 1

  def handlefiles(self, arg, dirname, filenames):
    for filename in filenames:
      pathname = os.path.join(dirname, filename)
      if not os.path.isdir(pathname):
        self.handlefile(pathname)

  def handledir(self, dirname):
    os.path.walk(dirname, self.handlefiles, None)

def main():
  # TODO: make this handle command line options using optparse...
  summarizer(sys.argv[1:])

