#!/usr/bin/env python

from translate.misc import multistring
from translate.misc import test_autoencode

class TestMultistring(test_autoencode.TestAutoencode):
    type2test = multistring.multistring

    def test_constructor(self):
        t = self.type2test
        s1 = t("test")
        assert type(s1) == t
        assert s1 == "test"
        assert s1.alt == ["test"]
        s2 = t(["test", "me"])
        assert type(s2) == t
        assert s2 == "test"
        assert s2.alt == ["test", "me"]
        assert s2 != s1

