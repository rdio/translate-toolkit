#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2005 Zuza Software Foundation
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

"""diff tool like GNU diff, but lets you have special options that are useful in dealing with PO files"""

import difflib
import optparse
import time
import os
import sys

lineterm = "\n"

def main():
    """main program for pydiff"""
    usage = "usage: %prog [options] fromfile tofile"
    parser = optparse.OptionParser(usage)
    parser.add_option("-l", "--lines", type="int", default=3, help='Set number of context lines (default 3)')
    parser.add_option("", "--fromcontains", type="string", default=None, help='Only include hunks where fromfile contains the given string')
    parser.add_option("", "--tocontains", type="string", default=None, help='Only include hunks where tofile contains the given string')
    parser.add_option("", "--contains", type="string", default=None, help='Only include hunks where fromfile or tofile contains the given string')
    (options, args) = parser.parse_args()

    n = options.lines
    fromfile, tofile = args

    fromfiledate = time.ctime(os.stat(fromfile).st_mtime)
    tofiledate = time.ctime(os.stat(tofile).st_mtime)
    fromlines = open(fromfile, 'U').readlines()
    tolines = open(tofile, 'U').readlines()
    outfile = sys.stdout

    matcher = difflib.SequenceMatcher(None, fromlines, tolines)
    groups = matcher.get_grouped_opcodes(n)
    started = False
    fromstring = '--- %s %s%s' % (fromfile, fromfiledate, lineterm)
    tostring = '+++ %s %s%s' % (tofile, tofiledate, lineterm)

    for group in groups:
        hunk = "".join([line for line in unified_diff(group, fromlines, tolines)])
        if options.fromcontains:
            hunk_from_lines = "".join(get_from_lines(group, fromlines))
            if options.fromcontains not in hunk_from_lines:
                continue
        if options.tocontains:
            hunk_to_lines = "".join(get_to_lines(group, tolines))
            if options.tocontains not in hunk_to_lines:
                continue
        if options.contains:
            hunk_lines = "".join(get_from_lines(group, fromlines) + get_to_lines(group, tolines))
            if options.tocontains not in hunk_lines:
                continue
        if not started:
            outfile.write(fromstring)
            outfile.write(tostring)
            started = True
        outfile.write(hunk)

def get_from_lines(group, a):
    """returns the lines referred to by group, from the fromfile"""
    from_lines = []
    for tag, i1, i2, j1, j2 in group:
        from_lines.extend(a[i1:i2])
    return from_lines

def get_to_lines(group, b):
    """returns the lines referred to by group, from the tofile"""
    to_lines = []
    for tag, i1, i2, j1, j2 in group:
        to_lines.extend(b[j1:j2])
    return to_lines

def unified_diff(group, a, b):
    """takes the group of opcodes and generates a unified diff line by line"""
    i1, i2, j1, j2 = group[0][1], group[-1][2], group[0][3], group[-1][4]
    yield "@@ -%d,%d +%d,%d @@%s" % (i1+1, i2-i1, j1+1, j2-j1, lineterm)
    for tag, i1, i2, j1, j2 in group:
        if tag == 'equal':
            for line in a[i1:i2]:
                yield ' ' + line
            continue
        if tag == 'replace' or tag == 'delete':
            for line in a[i1:i2]:
                yield '-' + line
        if tag == 'replace' or tag == 'insert':
            for line in b[j1:j2]:
                yield '+' + line

if __name__ == "__main__":
    main()

