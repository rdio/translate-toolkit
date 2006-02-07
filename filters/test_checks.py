# -*- coding: utf-8 -*-
from translate.filters import checks

def test_defaults():
    """tests default setup and that checks aren't altered by other constructions"""
    stdchecker = checks.StandardChecker()
    assert stdchecker.config.varmatches == []
    mozillachecker = checks.MozillaChecker()
    stdchecker = checks.StandardChecker()
    assert stdchecker.config.varmatches == []

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
    assert checks.fails(stdchecker.accelerators, "Mail &amp; News", "Pos en Nuus") 
    assert checks.passes(stdchecker.accelerators, "&Allow", u"&ﺲﻣﺎﺣ")
    kdechecker = checks.KdeChecker()
    assert checks.passes(kdechecker.accelerators, "&File", "&Fayile") 
    assert checks.fails(kdechecker.accelerators, "&File", "Fayile") 
    assert checks.fails(kdechecker.accelerators, "File", "&Fayile") 
    gnomechecker = checks.GnomeChecker()
    assert checks.passes(gnomechecker.accelerators, "_File", "_Fayile") 
    assert checks.fails(gnomechecker.accelerators, "_File", "Fayile") 
    assert checks.fails(gnomechecker.accelerators, "File", "_Fayile") 
    mozillachecker = checks.MozillaChecker()
    assert checks.passes(mozillachecker.accelerators, "&File", "&Fayile") 
    assert checks.fails(mozillachecker.accelerators, "&File", "Fayile") 
    assert checks.fails(mozillachecker.accelerators, "File", "&Fayile") 
    assert checks.passes(mozillachecker.accelerators, "Mail &amp; News", "Pos en Nuus") 
    assert checks.fails(mozillachecker.accelerators, "Mail &amp; News", "Pos en &Nuus") 
    ooochecker = checks.OpenOfficeChecker()
    assert checks.passes(ooochecker.accelerators, "~File", "~Fayile") 
    assert checks.fails(ooochecker.accelerators, "~File", "Fayile") 
    assert checks.fails(ooochecker.accelerators, "File", "~Fayile") 
    # Problems:
    # Accelerator before variable - see test_acceleratedvariables

def test_acceleratedvariables():
    """test for accelerated variables"""
    mozillachecker = checks.MozillaChecker()
    assert checks.fails(mozillachecker.acceleratedvariables, "%S &Options", "&%S Ikhetho")
    assert checks.passes(mozillachecker.acceleratedvariables, "%S &Options", "%S &Ikhetho")
    ooochecker = checks.OpenOfficeChecker()
    assert checks.fails(ooochecker.acceleratedvariables, "%PRODUCTNAME% ~Options", "~%PRODUCTNAME% Ikhetho")
    assert checks.passes(ooochecker.acceleratedvariables, "%PRODUCTNAME% ~Options", "%PRODUCTNAME% ~Ikhetho")
    

def test_accronyms():
    """tests acronyms"""
    stdchecker = checks.StandardChecker()
    assert checks.passes(stdchecker.acronyms, "An HTML file", "'n HTML leer")
    assert checks.fails(stdchecker.acronyms, "An HTML file", "'n LMTH leer")
    # We don't mind if you add an acronym to correct bad capitalisation in the original
    assert checks.passes(stdchecker.acronyms, "An html file", "'n HTML leer")
    # TODO We shouldn't worry about acronyms that appear in a musttranslate file
    #stdchecker = checks.StandardChecker(checks.CheckerConfig(musttranslatewords=["OK"]))
    #assert checks.passes(stdchecker.acronyms, "OK", "Kulungile")

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
    assert checks.fails(stdchecker.brackets, "For [sic] numbers", "Vier getalle")
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

def test_endpunc():
    """tests endpunc"""
    stdchecker = checks.StandardChecker()
    assert checks.passes(stdchecker.endpunc, "Question?", "Correct?")
    assert checks.fails(stdchecker.endpunc, " Question?", "Wrong ?")

def test_endwhitespace():
    """tests endwhitespace"""
    stdchecker = checks.StandardChecker()
    assert checks.passes(stdchecker.endwhitespace, "A setence. ", "I'm correct. ")
    assert checks.fails(stdchecker.endwhitespace, "A setence. ", "'I'm incorrect.")

def test_escapes():
    """tests escapes"""
    stdchecker = checks.StandardChecker()
    assert checks.passes(stdchecker.escapes, r"""_: KDE comment\n
A sentence""", "I'm correct.")
    assert checks.passes(stdchecker.escapes, r"A file\n", r"'n Leer\n")
    assert checks.fails(stdchecker.escapes, r"A file\n", r"'n Leer")
    assert checks.passes(stdchecker.escapes, r"A tab\t", r"'n Tab\t")
    assert checks.fails(stdchecker.escapes, r"A tab\t", r"'n Tab")
    assert checks.passes(stdchecker.escapes, r"An escape escape \\", r"Escape escape \\")
    assert checks.fails(stdchecker.escapes, r"An escape escape \\", r"Escape escape")
    assert checks.passes(stdchecker.escapes, r"A double quote \"", r"Double quote \"")
    assert checks.fails(stdchecker.escapes, r"A double quote \"", r"Double quote")

def test_filepaths():
    """tests filepaths"""
    stdchecker = checks.StandardChecker()
    assert checks.passes(stdchecker.filepaths, "%s to the file /etc/hosts on your system.", "%s na die leer /etc/hosts op jou systeem.")
    assert checks.fails(stdchecker.filepaths, "%s to the file /etc/hosts on your system.", "%s na die leer /etc/gasheer op jou systeem.")
    
def test_kdecomments():
    """tests kdecomments"""
    stdchecker = checks.StandardChecker()
    assert checks.passes(stdchecker.kdecomments, r"""_: I am a comment\n
A string to translate""", "'n String om te vertaal")
    assert checks.fails(stdchecker.kdecomments, r"""_: I am a comment\n
A string to translate""", r"""_: Ek is 'n commment\n
'n String om te vertaal""")

def test_long():
    """tests long messages"""
    stdchecker = checks.StandardChecker()
    assert checks.passes(stdchecker.long, "I am normal", "Ek is ook normaal")
    assert checks.fails(stdchecker.long, "Short.", "Kort.......................................................................................")

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
    # check that we can find words surrounded by punctuation
    assert checks.passes(stdchecker.musttranslatewords, "Click 'Mozilla' button", "Kliek 'Motzille' knoppie")
    assert checks.fails(stdchecker.musttranslatewords, "Click 'Mozilla' button", "Kliek 'Mozilla' knoppie")
    assert checks.passes(stdchecker.musttranslatewords, 'Click "Mozilla" button', 'Kliek "Motzille" knoppie')
    assert checks.fails(stdchecker.musttranslatewords, 'Click "Mozilla" button', 'Kliek "Mozilla" knoppie')
    assert checks.fails(stdchecker.musttranslatewords, 'Click "Mozilla" button', u'Kliek «Mozilla» knoppie')
    assert checks.passes(stdchecker.musttranslatewords, "Click (Mozilla) button", "Kliek (Motzille) knoppie")
    assert checks.fails(stdchecker.musttranslatewords, "Click (Mozilla) button", "Kliek (Mozilla) knoppie")
    assert checks.passes(stdchecker.musttranslatewords, "Click Mozilla!", "Kliek Motzille!")
    assert checks.fails(stdchecker.musttranslatewords, "Click Mozilla!", "Kliek Mozilla!")
    ## We need to define more word separators to allow us to find those hidden untranslated items
    #assert checks.fails(stdchecker.musttranslatewords, "Click OK", "Blah we-OK")


def test_notranslatewords():
    """tests stopwords"""
    stdchecker = checks.StandardChecker(checks.CheckerConfig(notranslatewords=[]))
    assert checks.passes(stdchecker.notranslatewords, "This uses Mozilla of course", "hierdie gebruik le mozille natuurlik")
    stdchecker = checks.StandardChecker(checks.CheckerConfig(notranslatewords=["Mozilla","Opera"]))
    assert checks.fails(stdchecker.notranslatewords, "This uses Mozilla of course", "hierdie gebruik le mozille natuurlik")
    assert checks.passes(stdchecker.notranslatewords, "This uses Mozilla of course", "hierdie gebruik Mozilla natuurlik")
    assert checks.fails(stdchecker.notranslatewords, "This uses Mozilla. Don't you?", "hierdie gebruik le mozille soos jy")
    assert checks.passes(stdchecker.notranslatewords, "This uses Mozilla. Don't you?", "hierdie gebruik Mozilla soos jy")
    # should always pass if there are no stopwords in the original
    assert checks.passes(stdchecker.notranslatewords, "This uses something else. Don't you?", "hierdie gebruik Mozilla soos jy")
    # Cope with commas
    assert checks.passes(stdchecker.notranslatewords, "using Mozilla Task Manager", u"šomiša Selaola Mošomo sa Mozilla, gomme")
    # Find words even if they are embedded in punctuation
    assert checks.fails(stdchecker.notranslatewords, "Click 'Mozilla' button", "Kliek 'Motzille' knoppie")
    assert checks.passes(stdchecker.notranslatewords, "Click 'Mozilla' button", "Kliek 'Mozilla' knoppie")
    assert checks.fails(stdchecker.notranslatewords, "Click Mozilla!", "Kliek Motzille!")
    assert checks.passes(stdchecker.notranslatewords, "Click Mozilla!", "Kliek Mozilla!")
    assert checks.fails(stdchecker.notranslatewords, "Searches (From Opera)", "adosako (kusukela ku- Ophera)")
    assert checks.fails(stdchecker.notranslatewords, "Searches (From Opera)", "adosako (kusukela ku- Ophera)")
    stdchecker = checks.StandardChecker(checks.CheckerConfig(notranslatewords=["Sun","NeXT"]))
    assert checks.fails(stdchecker.notranslatewords, "Sun/NeXT Audio", "Odio dza Ḓuvha/TeVHELAHO")
    assert checks.passes(stdchecker.notranslatewords, "Sun/NeXT Audio", "Odio dza Sun/NeXT")
    stdchecker = checks.StandardChecker(checks.CheckerConfig(notranslatewords=["sendmail"]))
    assert checks.fails(stdchecker.notranslatewords, "because 'sendmail' could", "ngauri 'rumelameiḽi' a yo")
    assert checks.passes(stdchecker.notranslatewords, "because 'sendmail' could", "ngauri 'sendmail' a yo")

def test_numbers():
    """test numbers"""
    stdchecker = checks.StandardChecker()
    assert checks.passes(stdchecker.numbers, "Netscape 4 was not as good as Netscape 7.", "Netscape 4 was nie so goed soos Netscape 7 nie.")
    # Check for correct detection of degree.  Also check that we aren't getting confused with 1 and 2 byte UTF-8 characters
    assert checks.fails(stdchecker.numbers, "180° turn", "180 turn")
    assert checks.passes(stdchecker.numbers, "180° turn", "180° turn")
    assert checks.fails(stdchecker.numbers, "180° turn", "360 turn")
    assert checks.fails(stdchecker.numbers, "180° turn", "360° turn")
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

def test_puncspacing():
    """tests spacing after punctuation"""
    stdchecker = checks.StandardChecker()
    assert checks.passes(stdchecker.puncspacing, "One, two, three.", "Kunye, kubili, kuthathu.")
    assert checks.passes(stdchecker.puncspacing, "One, two, three. ", "Kunye, kubili, kuthathu.")
    assert checks.fails(stdchecker.puncspacing, "One, two, three. ", "Kunye, kubili,kuthathu.")
    assert checks.passes(stdchecker.puncspacing, "One, two, three!?", "Kunye, kubili, kuthathu?")

def test_purepunc():
    """tests messages containing only punctuation"""
    stdchecker = checks.StandardChecker()
    assert checks.passes(stdchecker.purepunc, ".", ".")
    assert checks.fails(stdchecker.purepunc, ".", " ")

def test_sentencecount():
    """tests sentencecount messages"""
    stdchecker = checks.StandardChecker()
    assert checks.passes(stdchecker.sentencecount, "One. Two. Three.", "Een. Twee. Drie.")
    assert checks.fails(stdchecker.sentencecount, "One two three", "Een twee drie.")
    assert checks.fails(stdchecker.sentencecount, "One. Two. Three.", "Een Twee. Drie.")

def test_short():
    """tests short messages"""
    stdchecker = checks.StandardChecker()
    assert checks.passes(stdchecker.short, "I am normal", "Ek is ook normaal")
    assert checks.fails(stdchecker.short, "I am a very long sentence", "Ek")

def test_singlequoting():
    """tests single quotes"""
    stdchecker = checks.StandardChecker()
    assert checks.passes(stdchecker.singlequoting, "A 'Hot' plate", "Ipuleti 'elishisa' kunye")
    # FIXME this should pass but doesn't probably to do with our logic that got confused at the end of lines
    assert checks.passes(stdchecker.singlequoting, "'Hot' plate", "Ipuleti 'elishisa'")
    # FIXME newlines also confuse our algorithm for single quotes
    assert checks.passes(stdchecker.singlequoting, "File '%s'\n", "'%s' Faele\n")
    assert checks.fails(stdchecker.singlequoting, "'Hot' plate", "Ipuleti \"elishisa\"")
    assert checks.passes(stdchecker.singlequoting, "It's here.", "Dit is hier.")
    # We shouldn't see single quotes in KDE comments
    assert checks.passes(stdchecker.singlequoting, r"""_: 'Migrating' formats.\n
Converting...""", "Kugucula...")
    # Don't get confused by punctuation that touches a single quote
    assert checks.passes(stdchecker.singlequoting, "File '%s'.", "'%s' Faele.")
    assert checks.passes(stdchecker.singlequoting, "Blah 'format' blah.", "Blah blah 'sebopego'.")
    assert checks.passes(stdchecker.singlequoting, "Blah 'format' blah!", "Blah blah 'sebopego'!")
    assert checks.passes(stdchecker.singlequoting, "Blah 'format' blah?", "Blah blah 'sebopego'?")

def test_simplecaps():
    """tests simple caps"""
    # Simple caps is a very vauge test so the checks here are mostly for obviously fixable problem
    # or for checking obviously correct situations that are triggering a failure.
    stdchecker = checks.StandardChecker()
    # We should squash 'I' in the source text as it messes with capital detection
    assert checks.passes(stdchecker.simplecaps, "if you say I want", "as jy se ek wil")
    assert checks.passes(stdchecker.simplecaps, "MB of disk space for the cache.", "MB yendzawo yediski etsala.")

# def test_spellcheck():
#     """tests simple caps"""
#     stdchecker = checks.StandardChecker()

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

def test_startpunc():
    """tests startpunc"""
    stdchecker = checks.StandardChecker()
    assert checks.passes(stdchecker.startpunc, "<< Previous", "<< Correct")
    assert checks.fails(stdchecker.startpunc, " << Previous", "Wrong")

def test_startwhitespace():
    """tests startwhitespace"""
    stdchecker = checks.StandardChecker()
    assert checks.passes(stdchecker.startwhitespace, "A setence.", "I'm correct.")
    assert checks.fails(stdchecker.startwhitespace, " A setence.", "I'm incorrect.")

def test_unchanged():
    """tests unchanged entries"""
    stdchecker = checks.StandardChecker(checks.CheckerConfig(accelmarkers="&"))
    assert checks.fails(stdchecker.unchanged, "Unchanged", "Unchanged") 
    assert checks.fails(stdchecker.unchanged, "&Unchanged", "Un&changed") 
    assert checks.passes(stdchecker.unchanged, "Unchanged", "Changed") 
    assert checks.passes(stdchecker.unchanged, "1234", "1234") 
    assert checks.passes(stdchecker.unchanged, "I", "I") 
    assert checks.fails(stdchecker.unchanged, r"""_: KDE comment\n
Unchanged""", r"Unchanged") 
    # Variable only messages should be ignored
    mozillachecker = checks.MozillaChecker()
    assert checks.passes(mozillachecker.unchanged, "$ProgramName$", "$ProgramName$") 
    # Don't translate words should be ignored
    stdchecker = checks.StandardChecker(checks.CheckerConfig(notranslatewords=["Mozilla"]))
    assert checks.passes(mozillachecker.unchanged, "Mozilla", "Mozilla") 

def test_untranslated():
    """tests untranslated entries"""
    stdchecker = checks.StandardChecker()
    assert checks.fails(stdchecker.untranslated, "I am untranslated", "")
    assert checks.passes(stdchecker.untranslated, "I am translated", "Ek is vertaal")

def test_validchars():
    """tests valid characters"""
    stdchecker = checks.StandardChecker(checks.CheckerConfig())
    assert checks.passes(stdchecker.validchars, "The check always passes if you don't specify chars", "Die toets sal altyd werk as jy nie karacters specifisier")
    stdchecker = checks.StandardChecker(checks.CheckerConfig(validchars='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'))
    assert checks.passes(stdchecker.validchars, "This sentence contains valid characters", "Hierdie sin bevat ware karakters")
    assert checks.fails(stdchecker.validchars, "Some unexpected characters", "©®°±÷¼½¾")
    stdchecker = checks.StandardChecker(checks.CheckerConfig(validchars='⠁⠂⠃⠄⠅⠆⠇⠈⠉⠊⠋⠌⠍⠎⠏⠐⠑⠒⠓⠔⠕⠖⠗⠘⠙⠚⠛⠜⠝⠞⠟⠠⠡⠢⠣⠤⠥⠦⠧⠨⠩⠪⠫⠬⠭⠮⠯⠰'))
    assert checks.passes(stdchecker.validchars, "Our target language is all non-ascii", "⠁⠂⠃⠄⠆⠇⠈⠉⠜⠝⠞⠟⠠⠡⠢⠣⠤⠥⠦⠧⠨⠩⠪⠫")
    assert checks.fails(stdchecker.validchars, "Our target language is all non-ascii", "Some ascii⠁⠂⠃⠄⠆⠇⠈⠉⠜⠝⠞⠟⠠⠡⠢⠣⠤⠥⠦⠧⠨⠩⠪⠫")

def test_variables_kde():
    """tests variables in KDE translations"""
    # GNOME variables
    kdechecker = checks.KdeChecker()
    assert checks.passes(kdechecker.variables, "%d files of type %s saved.", "%d leers van %s tipe gestoor.")
    assert checks.fails(kdechecker.variables, "%d files of type %s saved.", "%s leers van %s tipe gestoor.")

def test_variables_gnome():
    """tests variables in GNOME translations"""
    # GNOME variables
    gnomechecker = checks.GnomeChecker()
    assert checks.passes(gnomechecker.variables, "%d files of type %s saved.", "%d leers van %s tipe gestoor.")
    assert checks.fails(gnomechecker.variables, "%d files of type %s saved.", "%s leers van %s tipe gestoor.")
    assert checks.passes(gnomechecker.variables, "Save $(file)", "Stoor $(file)")
    assert checks.fails(gnomechecker.variables, "Save $(file)", "Stoor $(leer)")

def test_variables_mozilla():
    """tests variables in Mozilla translations"""
    # Mozilla variables
    mozillachecker = checks.MozillaChecker()
    assert checks.passes(mozillachecker.variables, "Use the &brandShortname; instance.", "Gebruik die &brandShortname; weergawe.")
    assert checks.fails(mozillachecker.variables, "Use the &brandShortname; instance.", "Gebruik die &brandKortnaam; weergawe.")
    assert checks.passes(mozillachecker.variables, "Save %file%", "Stoor %file%")
    assert checks.fails(mozillachecker.variables, "Save %file%", "Stoor %leer%")
    assert checks.passes(mozillachecker.variables, "%d files of type %s saved.", "%d leers van %s tipe gestoor.")
    assert checks.fails(mozillachecker.variables, "%d files of type %s saved.", "%s leers van %s tipe gestoor.")
    assert checks.passes(mozillachecker.variables, "Save $file", "Stoor $file")
    assert checks.fails(mozillachecker.variables, "Save $file", "Stoor $leer")
    assert checks.passes(mozillachecker.variables, "About $ProgramName$", "Oor $ProgramName$")
    assert checks.fails(mozillachecker.variables, "About $ProgramName$", "Oor $NaamVanProgam$")
    # Double variable problem
    assert checks.fails(mozillachecker.variables, "Create In &lt;&lt;", "Etsa ka Ho &lt;lt;")
    # Variables at the end of a sentence
    assert checks.fails(mozillachecker.variables, "...time you start &brandShortName;.", "...lekgetlo le latelang ha o qala &LebitsoKgutshwane la kgwebo;.")
    # Ensure that we can detect two variables of the same name with one faulty
    assert checks.fails(mozillachecker.variables, "&brandShortName; successfully downloaded and installed updates. You will have to restart &brandShortName; to complete the update.", "&brandShortName; ḽo dzhenisa na u longela khwinifhadzo zwavhuḓi. Ni ḓo tea u thoma hafhu &DzinaḼipfufhi ḽa pfungavhuṇe; u itela u fhedzisa khwinifha dzo.")

def test_variables_openoffice():
    """tests variables in OpenOffice translations"""
    # OpenOffice.org variables
    ooochecker = checks.OpenOfficeChecker()
    assert checks.passes(ooochecker.variables, "Use the &brandShortname; instance.", "Gebruik die &brandShortname; weergawe.")
    assert checks.fails(ooochecker.variables, "Use the &brandShortname; instance.", "Gebruik die &brandKortnaam; weergawe.")
    assert checks.passes(ooochecker.variables, "Save %file%", "Stoor %file%")
    assert checks.fails(ooochecker.variables, "Save %file%", "Stoor %leer%")
    assert checks.passes(ooochecker.variables, "Save %file", "Stoor %file")
    assert checks.fails(ooochecker.variables, "Save %file", "Stoor %leer")
    assert checks.passes(ooochecker.variables, "Save $(file)", "Stoor $(file)")
    assert checks.fails(ooochecker.variables, "Save $(file)", "Stoor $(leer)")
    assert checks.passes(ooochecker.variables, "Save $file$", "Stoor $file$")
    assert checks.fails(ooochecker.variables, "Save $file$", "Stoor $leer$")
    assert checks.passes(ooochecker.variables, "Save ${file}", "Stoor ${file}")
    assert checks.fails(ooochecker.variables, "Save ${file}", "Stoor ${leer}")
    assert checks.passes(ooochecker.variables, "Save #file#", "Stoor #file#")
    assert checks.fails(ooochecker.variables, "Save #file#", "Stoor #leer#")
    assert checks.passes(ooochecker.variables, "Save ($file)", "Stoor ($file)")
    assert checks.fails(ooochecker.variables, "Save ($file)", "Stoor ($leer)")
    assert checks.passes(ooochecker.variables, "Save $[file]", "Stoor $[file]")
    assert checks.fails(ooochecker.variables, "Save $[file]", "Stoor $[leer]")
    assert checks.passes(ooochecker.variables, "Save [file]", "Stoor [file]")
    assert checks.fails(ooochecker.variables, "Save [file]", "Stoor [leer]")
    assert checks.passes(ooochecker.variables, "Save $file", "Stoor $file")
    assert checks.fails(ooochecker.variables, "Save $file", "Stoor $leer")
    # Variables hidden in KDE comments
    assert checks.passes(ooochecker.variables, r"""_: Do not translate %PROGRAMNAME% in the text\n
Start %PROGRAMNAME%""", "Begin %PROGRAMNAME%")

def test_xmltags():
    """tests xml tags"""
    stdchecker = checks.StandardChecker()
    assert checks.fails(stdchecker.xmltags, "Do it <b>now</b>", "Doen dit <v>nou</v>")
    assert checks.passes(stdchecker.xmltags, "Do it <b>now</b>", "Doen dit <b>nou</b>")
    assert checks.passes(stdchecker.xmltags, "Click <img src=\"img.jpg\">here</img>", "Klik <img src=\"img.jpg\">hier</img>")
    assert checks.fails(stdchecker.xmltags, "Click <img src=\"image.jpg\">here</img>", "Klik <img src=\"prent.jpg\">hier</img>")
    assert checks.passes(stdchecker.xmltags, "Start with the &lt;start&gt; tag", "Begin met die &lt;begin&gt;")
    #TODO: test tags like alt, longdsc that can be translated

def test_functions():
    """tests to see that funtions() are not translated"""
    stdchecker = checks.StandardChecker()
    assert checks.fails(stdchecker.functions, "blah rgb() blah", "blee brg() blee")
    assert checks.passes(stdchecker.functions, "blah rgb() blah", "blee rgb() blee")
    assert checks.fails(stdchecker.functions, "percentage in rgb()", "phesenthe kha brg()")
    assert checks.passes(stdchecker.functions, "percentage in rgb()", "phesenthe kha rgb()")
    assert checks.fails(stdchecker.functions, "rgb() in percentage", "brg() kha phesenthe")
    assert checks.passes(stdchecker.functions, "rgb() in percentage", "rgb() kha phesenthe")
    assert checks.fails(stdchecker.functions, "blah string.rgb() blah", "blee bleeb.rgb() blee")
    assert checks.passes(stdchecker.functions, "blah string.rgb() blah", "blee string.rgb() blee")

def test_emails():
    """tests to see that email addresses are not translated"""
    stdchecker = checks.StandardChecker()
    assert checks.fails(stdchecker.emails, "blah bob@example.net blah", "blee kobus@voorbeeld.net blee")
    assert checks.passes(stdchecker.emails, "blah bob@example.net blah", "blee bob@example.net blee")

def test_urls():
    """tests to see that URLs are not translated"""
    stdchecker = checks.StandardChecker()
    assert checks.fails(stdchecker.urls, "blah http://translate.org.za blah", "blee http://vertaal.org.za blee")
    assert checks.passes(stdchecker.urls, "blah http://translate.org.za blah", "blee http://translate.org.za blee")

def test_simpleplurals():
    """test that we can find English style plural(s)"""
    stdchecker = checks.StandardChecker()
    assert checks.fails(stdchecker.simpleplurals, "plural(s)", "meervoud(e)")
    assert checks.fails(stdchecker.simpleplurals, "Ungroup Metafile(s)...", "Kuvhanganyululani Metafaela(dzi)...")
