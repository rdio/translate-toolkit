# -*- coding: utf-8 -*-
from translate.filters import checks

def test_construct():
    """tests that the checkers can be constructed"""
    stdchecker = checks.StandardChecker()
    mozillachecker = checks.MozillaChecker()
    ooochecker = checks.OpenOfficeChecker()
    gnomechecker = checks.GnomeChecker()
    kdechecker = checks.KdeChecker()

def test_untranslatable():
    """tests stopwords"""
    stdchecker = checks.StandardChecker(checks.CheckerConfig(untranslatablewords=["Mozilla"]))
    assert stdchecker.untranslatable("This uses Mozilla of course", "hierdie gebruik le mozille natuurlik")
    assert not stdchecker.untranslatable("This uses Mozilla of course", "hierdie gebruik Mozilla natuurlik")
    assert stdchecker.untranslatable("This uses Mozilla. Don't you?", "hierdie gebruik le mozille soos jy")
    assert not stdchecker.untranslatable("This uses Mozilla. Don't you?", "hierdie gebruik Mozilla soos jy")

