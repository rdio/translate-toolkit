# -*- coding: iso-8859-1 -*-
""" Test script for the Unicode implementation.

Written by Marc-Andre Lemburg (mal@lemburg.com).

(c) Copyright CNRI, All Rights Reserved. NO WARRANTY.

"""#"
from translate.misc import autoencode

class TestAutoencode:
    type2test = autoencode.autoencode

    def test_default_encoding(self):
        s = self.type2test(u'unicode string', 'utf-8')
        assert s.encoding == 'utf-8'
        assert str(s) == 'unicode string'
        s = self.type2test(u'\u20ac')
	assert str(self.type2test(u'\u20ac', 'utf-8')) == '\xe2\x82\xac'

