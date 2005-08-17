# -*- coding: utf-8 -*-
from translate.filters import checks

def test_construct():
    """tests that the checkers can be constructed"""
    stdchecker = checks.StandardChecker()
    mozillachecker = checks.MozillaChecker()
    ooochecker = checks.OpenOfficeChecker()
    gnomechecker = checks.GnomeChecker()
    kdechecker = checks.KdeChecker()

def test_notranslatewords():
    """tests stopwords"""
    stdchecker = checks.StandardChecker(checks.CheckerConfig(notranslatewords=[]))
    assert stdchecker.notranslatewords("This uses Mozilla of course", "hierdie gebruik le mozille natuurlik")
    stdchecker = checks.StandardChecker(checks.CheckerConfig(notranslatewords=["Mozilla"]))
    assert not stdchecker.notranslatewords("This uses Mozilla of course", "hierdie gebruik le mozille natuurlik")
    assert stdchecker.notranslatewords("This uses Mozilla of course", "hierdie gebruik Mozilla natuurlik")
    assert not stdchecker.notranslatewords("This uses Mozilla. Don't you?", "hierdie gebruik le mozille soos jy")
    assert stdchecker.notranslatewords("This uses Mozilla. Don't you?", "hierdie gebruik Mozilla soos jy")
    # should always pass if there are no stopwords in the original
    assert stdchecker.notranslatewords("This uses something else. Don't you?", "hierdie gebruik Mozilla soos jy")

def test_musttranslatewords():
    """tests stopwords"""
    stdchecker = checks.StandardChecker(checks.CheckerConfig(musttranslatewords=[]))
    assert stdchecker.musttranslatewords("This uses Mozilla of course", "hierdie gebruik le mozille natuurlik")
    stdchecker = checks.StandardChecker(checks.CheckerConfig(musttranslatewords=["Mozilla"]))
    assert stdchecker.musttranslatewords("This uses Mozilla of course", "hierdie gebruik le mozille natuurlik")
    assert not stdchecker.musttranslatewords("This uses Mozilla of course", "hierdie gebruik Mozilla natuurlik")
    assert stdchecker.musttranslatewords("This uses Mozilla. Don't you?", "hierdie gebruik le mozille soos jy")
    assert not stdchecker.musttranslatewords("This uses Mozilla. Don't you?", "hierdie gebruik Mozilla soos jy")
    # should always pass if there are no stopwords in the original
    assert stdchecker.notranslatewords("This uses something else. Don't you?", "hierdie gebruik Mozilla soos jy")

