# -*- coding: utf-8 -*-
# 
# Copyright 2006 Zuza Software Foundation
# 
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""A class that does terminology matching"""

from translate.search import segment
import math

class TerminologyComparer:
    def __init__(self, max_len=500):
        self.MAX_LEN = max_len

    def similarity(self, a, b, stoppercentage=40):
        """returns the match quality of term b in the text a"""
        print a, b
#        wrd_a = segment.words(a)
#        wrd_b = segment.words(b)
#        if len(wrd_a) + len(wrd_b) > 2:
#            similarity += self.similarity_real(wrd_a, wrd_b, 0)
#            measurements += 1
	if b in a:
            print "%s in %s" % (b, a)
            return 100
        else:
            return 0

