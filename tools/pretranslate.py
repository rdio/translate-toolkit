#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2008 Zuza Software Foundation
# 
# This file is part of translate.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""fill localization files with suggested translations based on
translation memory and existing translations
"""

from translate.storage import factory
from translate.search import match


# We don't want to reinitialise the TM each time, so let's store it here.
tmmatcher = None


def memory(tmfiles, max_candidates=1, min_similarity=75, max_length=1000):
    """Returns the TM store to use. Only initialises on first call."""
    global tmmatcher
    # Only initialise first time
    if tmmatcher is None:
        if isinstance(tmfiles, list):
            tmstore = [factory.getobject(tmfile) for tmfile in tmfiles]
        else:
            tmstore = factory.getobject(tmfiles)
        tmmatcher = match.matcher(tmstore, max_candidates=max_candidates, min_similarity=min_similarity, max_length=max_length)
    return tmmatcher


def pretranslate_file(input_file, output_file, template_file, tm=None, min_similarity=75, fuzzymatching=True):
    """pretranslate any factory supported file with old translations and translation memory"""
    input_store = factory.getobject(input_file)
    template_store = None
    if template_file is not None:
        template_store = factory.getobject(template_file)
    output = pretranslate_store(input_store, template_store, tm, min_similarity, fuzzymatching)
    output_file.write(str(output))
    return 1


def match_template_id (input_unit, template_store):
    """returns a matching unit from a template"""
    #since oo2po and moz2po use localtion as unique identifiers for strings
    #we match against location first, then check for matching source strings
    #FIXME: this makes absolutely no sense for other po files
    for location in input_unit.getlocations():
        matching_unit = template_store.locationindex.get(location, None)
        #do we really want to discard units with matching locations but no matching source?
        if matching_unit is not None and matching_unit.source == input_unit.source and len(matching_unit.target) > 0:
            return matching_unit
        else:
            #if no match by location information search for identical source strings
            #FIXME: need a better method for matching strings, we don't take context into account
            #FIXME: need a better test for when not to use location info for matching
            return template_store.findunit(input_unit.source)


def match_fuzzy(input_unit, matchers):
    """returns a fuzzy match from a queue of matchers"""
    for matcher in matchers:
        fuzzycandidates = matcher.matches(input_unit.source)
        if fuzzycandidates:
            return fuzzycandidates[0]


def pretranslate_unit(input_unit, template_store, matchers=None, mark_reused=False) :
    """returns a pretranslated unit, if no translation was found return input unit unchanged"""
    matching_unit = None
    #do template matching
    if template_store:
        matching_unit = match_template_id(input_unit, template_store)
        
        if matching_unit is not None and len(matching_unit.target) > 0:
            input_unit.merge(matching_unit, authoritative=True)

    #do fuzzy matching
    if matching_unit is None and matchers:
        matching_unit = match_fuzzy(input_unit, matchers)
            
        if matching_unit and len(matching_unit.target) > 0: 
            input_unit.merge(matching_unit)
            if mark_reused:
                original_unit = template_store.findunit(matching_unit.source)
                original_unit.reused = True

    return input_unit


def pretranslate_store(input_store, template_store, tm=None, min_similarity=75, fuzzymatching=True):
    """does the actual pretranslation"""

    #preperation
    matchers = []
    #prepare template
    if template_store is not None:
        template_store.makeindex()
        #do we want to consider obsolete translations?
        for unit in template_store.units:
            if unit.isobsolete():
                unit.resurrect()

        if fuzzymatching:
            #create template matcher
            #FIXME: max_length hardcoded
            matcher = match.matcher(template_store, max_candidates=1, min_similarity=min_similarity, max_length=3000, usefuzzy=True)
            matcher.addpercentage = False
            matchers.append(matcher)

    #prepare tm    
    #create tm matcher
    if tm and fuzzymatching:
        #FIXME: max_length hardcoded
        matcher = memory(tm, max_candidates=1, min_similarity=min_similarity, max_length=1000)
        matcher.addpercentage = False
        matchers.append(matcher)
    
    #main loop
    for input_unit in input_store.units:
        if  input_unit.istranslatable():
            input_unit = pretranslate_unit(input_unit, template_store, matchers)
    
    return input_store


def main(argv=None):
    from translate.convert import convert
    formats = {"pot": ("po", pretranslate_file), ("pot", "po"): ("po", pretranslate_file),
               "po": ("po", pretranslate_file), ("po", "po"): ("po", pretranslate_file),
               "xlf": ("xlf", pretranslate_file), ("xlf", "xlf"): ("xlf", pretranslate_file),
               }
    parser = convert.ConvertOptionParser(formats, usetemplates=True, 
        allowmissingtemplate=True, description=__doc__)
    parser.add_option("", "--tm", dest="tm", default=None,
        help="The file to use as translation memory when fuzzy matching")
    parser.passthrough.append("tm")
    defaultsimilarity = 75
    parser.add_option("-s", "--similarity", dest="min_similarity", default=defaultsimilarity,
        type="float", help="The minimum similarity for inclusion (default: %d%%)" % defaultsimilarity)
    parser.passthrough.append("min_similarity")
    parser.add_option("--nofuzzymatching", dest="fuzzymatching", action="store_false", 
        default=True, help="Disable fuzzy matching")
    parser.passthrough.append("fuzzymatching")
    parser.run(argv)


if __name__ == '__main__':
    main()
