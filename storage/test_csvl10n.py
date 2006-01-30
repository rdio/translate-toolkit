#!/usr/bin/env python

from translate.storage import csvl10n
from translate.storage import test_base
from translate.misc import wStringIO

class TestCSVUnit(test_base.TestTranslationUnit):
    UnitClass = csvl10n.csvunit

class TestCSV(test_base.TestTranslationStore):
    StoreClass = csvl10n.csvfile
