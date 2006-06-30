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
#

"""Class to perform translation memory matching from a store of translation units"""

import Levenshtein
import heapq
from translate.storage import base

def usable(unit):
    """Returns whether this translation unit is usable for TM"""
    #TODO: We might want to consider more attributes, such as approved, reviewed, etc.
    if unit.source and unit.target and not unit.isfuzzy():
        return True
    return False

class matcher:
    """A class that will do matching and store configuration for the matching process"""
    def __init__(self, store, max_candidates=10, min_similarity=75, comparer=None):
        """max_candidates is the maximum number of candidates that should be assembled,
        min_similarity is the minimum similarity that must be attained to be included in
        the result, comparer is an optional Comparer with similarity() function"""
        if comparer is None:
            comparer = Levenshtein.LevenshteinComparer()
        self.comparer = comparer
        self.setparameters(max_candidates, min_similarity)
        self.inittm(store)
        
    def inittm(self, store):
        """Initialises the memory for later use. We use simple base units for 
        speedup."""
        self.candidates = []
        candidates = filter(usable, store.units)
        for candidate in candidates:
            simpleunit = base.TranslationUnit(candidate.source)
            simpleunit.target = candidate.target
            self.candidates.append(simpleunit)

    def setparameters(self, max_candidates=10, min_similarity=75):
        """Sets the parameters without reinitialising the tm. If a parameter 
        is not specified, it is set to the default, not ignored"""
        self.MAX_CANDIDATES = max_candidates
        self.MIN_SIMILARITY = min_similarity
            
    def matches(self, text):
        """Returns a list of possible matches for text in candidates with the associated similarity.
        Return value is a list containing tuples (score, original, translation)."""
        bestcandidates = [(0.0,"","")]*self.MAX_CANDIDATES
        heapq.heapify(bestcandidates)
        #We use self.MIN_SIMILARITY, but if we already know we have max_candidates
        #that are better, we can adjust min_similarity upwards for speedup
        min_similarity = self.MIN_SIMILARITY
        for candidate in self.candidates:
            cmpstring = candidate.source
            targetstring = candidate.target
            similarity = self.comparer.similarity(text, cmpstring, min_similarity)
            if similarity < min_similarity:
                continue
            lowestscore = bestcandidates[0][0]
            if similarity > lowestscore:
                heapq.heapreplace(bestcandidates, (similarity, cmpstring, targetstring))
                if min_similarity < bestcandidates[0][0]:
                    min_similarity = bestcandidates[0][0]
        
        #Remove the empty ones:
        def notzero(item):
            score = item[0]
            return score != 0
        bestcandidates = filter(notzero, bestcandidates)
        #Sort for use as a general list, and reverse so the best one is at index 0
        bestcandidates.sort(reverse=True)
        return bestcandidates


