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

def test_brackets():
    """tests brackets"""
    stdchecker = checks.StandardChecker()
    assert checks.passes(stdchecker.brackets, "N number(s)", "N getal(le)")
    assert checks.fails(stdchecker.brackets, "For {sic} numbers", "Vier getalle")
    assert checks.fails(stdchecker.brackets, "For }sic{ numbers", "Vier getalle")
    #assert checks.fails(stdchecker.brackets, "For [sic] numbers", "Vier getalle")
    assert checks.fails(stdchecker.brackets, "For ]sic[ numbers", "Vier getalle")
    assert checks.passes(stdchecker.brackets, "{[(", "[({")

def test_compendiumconflicts():
    """tests compendiumconflicts"""
    stdchecker = checks.StandardChecker()
    assert checks.fails(stdchecker.compendiumconflicts, "File not saved", r"""#-#-#-#-# file1.po #-#-#-#-#\n
Leer nie gestoor gestoor nie\n
#-#-#-#-# file1.po #-#-#-#-#\n
Leer nie gestoor""")

def test_doublequoting():
    """tests double quotes"""
    stdchecker = checks.StandardChecker()
    assert checks.fails(stdchecker.doublequoting, "Hot plate", "\"Ipuleti\" elishisa")
    assert checks.passes(stdchecker.doublequoting, "\"Hot\" plate", "\"Ipuleti\" elishisa")
    assert checks.fails(stdchecker.doublequoting, "'Hot' plate", "\"Ipuleti\" elishisa")
    assert checks.passes(stdchecker.doublequoting, "\\\"Hot\\\" plate", "\\\"Ipuleti\\\" elishisa")
    
def test_doublespacing():
    """tests double spacing"""
    stdchecker = checks.StandardChecker()
    assert checks.passes(stdchecker.doublespacing, "Sentence.  Another sentence.", "Sin.  'n Ander sin.")
    assert checks.passes(stdchecker.doublespacing, "Sentence. Another sentence.", "Sin. No double spacing.")
    assert checks.fails(stdchecker.doublespacing, "Sentence.  Another sentence.", "Sin. Missing the double space.")
    assert checks.fails(stdchecker.doublespacing, "Sentence. Another sentence.", "Sin.  Uneeded double space in translation.")

def test_doublewords():
    """tests doublewords"""
    stdchecker = checks.StandardChecker()
    assert checks.passes(stdchecker.doublewords, "Save the rhino", "Save the rhino")
    assert checks.fails(stdchecker.doublewords, "Save the rhino", "Save the the rhino")
    # Double variables are not an error
    #stdchecker = checks.StandardChecker(checks.CheckerConfig(varmatches=[("%", 1)]))
    #assert checks.passes(stdchecker.doublewords, "%s %s installation", "tsenyo ya %s %s")

def test_filepaths():
    """tests filepaths"""
    stdchecker = checks.StandardChecker()
    assert checks.passes(stdchecker.filepaths, "%s to the file /etc/hosts on your system.", "%s na die leer /etc/hosts op jou systeem.")
    assert checks.fails(stdchecker.filepaths, "%s to the file /etc/hosts on your system.", "%s na die leer /etc/gasheer op jou systeem.")
    
def test_numbers():
    """test numbers"""
    stdchecker = checks.StandardChecker()
    assert checks.passes(stdchecker.numbers, "Netscape 4 was not as good as Netscape 7.", "Netscape 4 was nie so goed soos Netscape 7 nie.")
    # Check for correct detection of degree.  Also check that we aren't getting confused with 1 and 2 byte UTF-8 characters
    assert checks.fails(stdchecker.numbers, "180° turn", "180 turn")
    assert checks.passes(stdchecker.numbers, "180~ turn", "180 turn")
    assert checks.passes(stdchecker.numbers, "180¶ turn", "180 turn")
    # Numbers with multiple decimal points
    assert checks.passes(stdchecker.numbers, "12.34.56", "12.34.56")
    assert checks.fails(stdchecker.numbers, "12.34.56", "98.76.54")
    # Currency
    # FIXME we should probably be able to handle currency checking with locale inteligence
    assert checks.passes(stdchecker.numbers, "R57.60", "R57.60")
    # FIXME - again locale intelligence should allow us to use other decimal seperators
    assert checks.fails(stdchecker.numbers, "R57.60", "R57,60")
    assert checks.fails(stdchecker.numbers, "1,000.00", "1 000,00")

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

def test_puncspacing():
    """tests spacing after punctuation"""
    stdchecker = checks.StandardChecker()
    assert checks.passes(stdchecker.puncspacing, "One, two, three.", "Kunye, kubili, kuthathu.")
    assert checks.passes(stdchecker.puncspacing, "One, two, three. ", "Kunye, kubili, kuthathu.")
    assert checks.fails(stdchecker.puncspacing, "One, two, three. ", "Kunye, kubili,kuthathu.")
    assert checks.passes(stdchecker.puncspacing, "One, two, three!?", "Kunye, kubili, kuthathu?")

def test_short():
    """tests short messages"""
    stdchecker = checks.StandardChecker()
    assert checks.passes(stdchecker.short, "I am normal", "Ek is ook normaal")
    assert checks.fails(stdchecker.short, "I am a very long sentence", "Ek")

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

def test_untranslated():
    """tests untranslated entries"""
    stdchecker = checks.StandardChecker()
    assert checks.fails(stdchecker.untranslated, "I am untranslated", "")
    assert checks.passes(stdchecker.untranslated, "I am translated", "Ek is vertaal")

def test_xmltags():
    """tests xml tags"""
    stdchecker = checks.StandardChecker()
    assert checks.fails(stdchecker.xmltags, "Do it <b>now</b>", "Doen dit <v>nou</v>")
    assert checks.passes(stdchecker.xmltags, "Do it <b>now</b>", "Doen dit <b>nou</b>")
    assert checks.passes(stdchecker.xmltags, "Click <img src=\"img.jpg\">here</img>", "Klik <img src=\"img.jpg\">hier</img>")
    assert checks.fails(stdchecker.xmltags, "Click <img src=\"image.jpg\">here</img>", "Klik <img src=\"prent.jpg\">hier</img>")
    assert checks.passes(stdchecker.xmltags, "Start with the &lt;start&gt; tag", "Begin met die &lt;begin&gt;")
    #TODO: test tags like alt, longdsc that can be translated
