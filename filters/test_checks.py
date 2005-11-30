# -*- coding: utf-8 -*-
from translate.filters import checks

def test_construct():
    """tests that the checkers can be constructed"""
    stdchecker = checks.StandardChecker()
    mozillachecker = checks.MozillaChecker()
    ooochecker = checks.OpenOfficeChecker()
    gnomechecker = checks.GnomeChecker()
    kdechecker = checks.KdeChecker()

def test_accelerators():
    """tests accelerators"""
    stdchecker = checks.StandardChecker(checks.CheckerConfig(accelmarkers="&"))
    assert checks.passes(stdchecker.accelerators, "&File", "&Fayile") 
    assert checks.fails(stdchecker.accelerators, "&File", "Fayile") 
    assert checks.fails(stdchecker.accelerators, "File", "&Fayile") 
    assert checks.passes(stdchecker.accelerators, "Mail && News", "Pos en Nuus") 
    assert checks.passes(stdchecker.accelerators, "Mail &amp; News", "Pos en Nuus") 
    assert checks.passes(stdchecker.accelerators, "&Allow", u"&ﺲﻣﺎﺣ")

def test_accronyms():
    """tests acronyms"""
    stdchecker = checks.StandardChecker()
    assert checks.passes(stdchecker.acronyms, "An HTML file", "'n HTML leer")
    assert checks.fails(stdchecker.acronyms, "An HTML file", "'n LMTH leer")
    # We don't mind if you add an acronym to correct bad capitalisation in the original
    assert checks.passes(stdchecker.acronyms, "An html file", "'n HTML leer")

def test_blank():
    """tests blank"""
    stdchecker = checks.StandardChecker()
    assert checks.fails(stdchecker.blank, "Save as", " ")

def test_compendiumconflicts():
    """tests compendiumconflicts"""
    stdchecker = checks.StandardChecker()
    assert checks.fails(stdchecker.compendiumconflicts, "File not saved", """#-#-#-#-# file1.po #-#-#-#-#\\n
Leer nie gestoor gestoor nie\\n
#-#-#-#-# file1.po #-#-#-#-#\\n
Leer nie gestoor""")

def test_notranslatewords():
    """tests stopwords"""
    stdchecker = checks.StandardChecker(checks.CheckerConfig(notranslatewords=[]))
    assert checks.passes(stdchecker.notranslatewords, "This uses Mozilla of course", "hierdie gebruik le mozille natuurlik")
    stdchecker = checks.StandardChecker(checks.CheckerConfig(notranslatewords=["Mozilla"]))
    assert checks.fails(stdchecker.notranslatewords, "This uses Mozilla of course", "hierdie gebruik le mozille natuurlik")
    assert checks.passes(stdchecker.notranslatewords, "This uses Mozilla of course", "hierdie gebruik Mozilla natuurlik")
    assert checks.fails(stdchecker.notranslatewords, "This uses Mozilla. Don't you?", "hierdie gebruik le mozille soos jy")
    assert checks.passes(stdchecker.notranslatewords, "This uses Mozilla. Don't you?", "hierdie gebruik Mozilla soos jy")
    # should always pass if there are no stopwords in the original
    assert checks.passes(stdchecker.notranslatewords, "This uses something else. Don't you?", "hierdie gebruik Mozilla soos jy")

def test_musttranslatewords():
    """tests stopwords"""
    stdchecker = checks.StandardChecker(checks.CheckerConfig(musttranslatewords=[]))
    assert checks.passes(stdchecker.musttranslatewords, "This uses Mozilla of course", "hierdie gebruik le mozille natuurlik")
    stdchecker = checks.StandardChecker(checks.CheckerConfig(musttranslatewords=["Mozilla"]))
    assert checks.passes(stdchecker.musttranslatewords, "This uses Mozilla of course", "hierdie gebruik le mozille natuurlik")
    assert checks.fails(stdchecker.musttranslatewords, "This uses Mozilla of course", "hierdie gebruik Mozilla natuurlik")
    assert checks.passes(stdchecker.musttranslatewords, "This uses Mozilla. Don't you?", "hierdie gebruik le mozille soos jy")
    assert checks.fails(stdchecker.musttranslatewords, "This uses Mozilla. Don't you?", "hierdie gebruik Mozilla soos jy")
    # should always pass if there are no stopwords in the original
    assert checks.passes(stdchecker.musttranslatewords, "This uses something else. Don't you?", "hierdie gebruik Mozilla soos jy")

def test_startcaps():
    """tests starting capitals"""
    stdchecker = checks.StandardChecker()
    assert checks.passes(stdchecker.startcaps, "Find", "Vind")
    assert checks.passes(stdchecker.startcaps, "find", "vind")
    assert checks.fails(stdchecker.startcaps, "Find", "vind")
    assert checks.fails(stdchecker.startcaps, "find", "Vind")
    # Need to check for prefilters ie test that won't be run if translation is blank
    #assert checks.passes(stdchecker.startcaps, "Find", "")
    assert checks.fails(stdchecker.startcaps, "Find", "'")
    assert checks.fails(stdchecker.startcaps, "'", "Find")
    assert checks.passes(stdchecker.startcaps, "'", "'")
    assert checks.passes(stdchecker.startcaps, "\\.,/?!`'\"[]{}()@#$%^&*_-;:<>Find", "\\.,/?!`'\"[]{}()@#$%^&*_-;:<>Vind")
    # With leading whitespace
    assert checks.passes(stdchecker.startcaps, " Find", " Vind")
    assert checks.passes(stdchecker.startcaps, " find", " vind")
    assert checks.fails(stdchecker.startcaps, " Find", " vind")
    assert checks.fails(stdchecker.startcaps, " find", " Vind")
    # Leading punctuation
    assert checks.passes(stdchecker.startcaps, "'Find", "'Vind")
    assert checks.passes(stdchecker.startcaps, "'find", "'vind")
    assert checks.fails(stdchecker.startcaps, "'Find", "'vind")
    assert checks.fails(stdchecker.startcaps, "'find", "'Vind")
    # Unicode
    assert checks.passes(stdchecker.startcaps, "Find", u"Šind")
    assert checks.passes(stdchecker.startcaps, "find", u"šind")
    assert checks.fails(stdchecker.startcaps, "Find", u"šind")
    assert checks.fails(stdchecker.startcaps, "find", u"Šind")
    # Accelerators
    stdchecker = checks.StandardChecker(checks.CheckerConfig(accelmarkers="&"))
    assert checks.passes(stdchecker.startcaps, "&Find", "Vi&nd")

def test_unchanged():
    """tests unchanged entries"""
    stdchecker = checks.StandardChecker()
    assert checks.fails(stdchecker.unchanged, "Unchanged", "Unchanged") 
    assert checks.passes(stdchecker.unchanged, "Unchanged", "Changed") 
    # Should be filtering out KDE comments before testing
    #assert checks.fails(stdchecker.unchanged, "_: KDE comment\\nUnchanged", "Unchanged") 


