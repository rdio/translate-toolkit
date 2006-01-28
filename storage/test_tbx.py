#!/usr/bin/env python

from translate.storage import tbx
from translate.misc import wStringIO

class TestTMXUnit:
	def test_equality(self):
		unit1 = tbx.tbxunit("Term1")
		unit2 = tbx.tbxunit("Term1")
		unit3 = tbx.tbxunit("Term2")
		assert unit1 == unit2
		assert unit1 != unit3

class TestTMXfile:
#	def tbxparse(self, tbxsource):
#		"""helper that parses tbx source without requiring a file"""
#		tbxfile = tbx.tbxfile.parsestring(tbxsource)
#		return tbxfile

	def test_basic(self):
		tbxfile = tbx.tbxfile()
		assert tbxfile.units == []
		tbxfile.addsourceunit("Bla")
		assert len(tbxfile.units) == 1
		newfile = tbx.tbxfile.parsestring(str(tbxfile))
		print str(tbxfile)
		assert len(newfile.units) == 1
		assert newfile.units[0].source == "Bla"
		assert newfile.findunit("Bla").source == "Bla"
#		assert newfile.findunit("dit") is None

	def test_source(self):
		tbxfile = tbx.tbxfile()
		tbxunit = tbxfile.addsourceunit("Concept")
		tbxunit.setsource("Term")
		newfile = tbx.tbxfile.parsestring(str(tbxfile))
		print str(tbxfile)
		assert newfile.findunit("Concept") is None
		assert newfile.findunit("Term") is not None
	
	def test_target(self):
		tbxfile = tbx.tbxfile()
		tbxunit = tbxfile.addsourceunit("Concept")
		#tbxunit.target = "Konsep"
		tbxunit.settarget("Konsep")
		newfile = tbx.tbxfile.parsestring(str(tbxfile))
		print str(tbxfile)
		assert newfile.findunit("Concept").target == "Konsep"
		
