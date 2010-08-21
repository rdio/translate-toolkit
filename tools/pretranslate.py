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

"""Fill localization files with suggested translations based on
translation memory and existing translations.
"""

from translate.storage import factory
from translate.storage import xliff
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
    """Pretranslate any factory supported file with old translations and translation memory."""
    input_store = factory.getobject(input_file)
    template_store = None
    if template_file is not None:
        template_store = factory.getobject(template_file)

    output = pretranslate_store(input_store, template_store, tm, min_similarity, fuzzymatching)
    output_file.write(str(output))
    return 1


def match_template_id(input_unit, template_store):
    """Returns a matching unit from a template."""
    # we want to use slightly different matching strategies for PO files
    # generated by our own moz2po and oo2po. Let's take a cheap shot at
    # detecting them from the presence of a ':' in the first location.
    locations = input_unit.getlocations()
    if not locations or ":" in locations[0]:
        # do normal gettext-like matching
        matching_unit = template_store.findid(input_unit.getid())
        return matching_unit

    else:
        #since oo2po and moz2po use location as unique identifiers for strings
        #we match against location first, then check for matching source strings
        #this makes no sense for normal gettext files
        for location in locations:
            matching_unit = template_store.locationindex.get(location, None)
            #do we really want to discard units with matching locations but no matching source?
            if matching_unit is not None and matching_unit.source == input_unit.source and matching_unit.gettargetlen() > 0:
                return matching_unit


def match_fuzzy(input_unit, matchers):
    """Return a fuzzy match from a queue of matchers."""
    for matcher in matchers:
        fuzzycandidates = matcher.matches(input_unit.source)
        if fuzzycandidates:
            return fuzzycandidates[0]


def pretranslate_unit(input_unit, template_store, matchers=None, mark_reused=False):
    """Pretranslate a unit or return unchanged if no translation was found."""

    matching_unit = None
    #do template matching
    if template_store:
        matching_unit = match_template_id(input_unit, template_store)

    if matching_unit and matching_unit.gettargetlen() > 0:
        input_unit.merge(matching_unit, authoritative=True)
    elif matchers:
        #do fuzzy matching
        matching_unit = match_fuzzy(input_unit, matchers)
        if matching_unit and matching_unit.gettargetlen() > 0:
            #FIXME: should we dispatch here instead of this crude type check
            if isinstance(input_unit, xliff.xliffunit):
                #FIXME: what about origin, lang and matchquality
                input_unit.addalttrans(matching_unit.target, origin="fish", sourcetxt=matching_unit.source)
            else:
                input_unit.merge(matching_unit, authoritative=True)

    #FIXME: ugly hack required by pot2po to mark old
    #translations reused for new file. loops over
    if mark_reused and matching_unit and template_store:
        original_unit = template_store.findunit(matching_unit.source)
        if original_unit is not None:
            original_unit.reused = True

    return input_unit

def prepare_template_pofile(template_store):
    """PO format specific template preparation logic."""
    #do we want to consider obsolete translations?
    for unit in template_store.units:
        if unit.isobsolete():
            unit.resurrect()

def pretranslate_store(input_store, template_store, tm=None, min_similarity=75, fuzzymatching=True):
    """Do the actual pretranslation of a whole store."""
    #preperation
    matchers = []
    #prepare template
    if template_store is not None:
        template_store.makeindex()
        #template preparation based on type
        prepare_template = "prepare_template_%s" % template_store.__class__.__name__
        if prepare_template in globals():
            globals()[prepare_template](template_store)

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
