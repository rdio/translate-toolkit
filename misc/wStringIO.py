#!/usr/bin/env python
# 
# Copyright 2002, 2003 Zuza Software Foundation
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

"""A wrapper for cStringIO that provides more of the functions of StringIO at the speed of cStringIO"""

import cStringIO

class StringIO:
    def __init__(self, buf = ''):
        if not isinstance(buf, basestring):
            buf = str(buf)
        self.len = len(buf)
        self.buf = cStringIO.StringIO()
        self.buf.write(buf)
        self.buf.seek(0)
        self.pos = 0
        self.closed = 0

    def __iter__(self):
        return self

    def next(self):
        if self.closed:
            raise StopIteration
        r = self.readline()
        if not r:
            raise StopIteration
        return r

    def close(self):
        """Free the memory buffer.
        """
        if not self.closed:
            self.closed = 1
            del self.buf, self.pos

    def isatty(self):
        if self.closed:
            raise ValueError, "I/O operation on closed file"
        return False

    def seek(self, pos, mode = 0):
        if self.closed:
            raise ValueError, "I/O operation on closed file"
        self.buf.seek(pos, mode)
        self.pos = self.buf.tell()

    def tell(self):
        if self.closed:
            raise ValueError, "I/O operation on closed file"
        return self.pos

    def read(self, n = None):
        if self.closed:
            raise ValueError, "I/O operation on closed file"
        if n == None:
          r = self.buf.read()
        else:
          r = self.buf.read(n)
        self.pos = self.buf.tell()
        return r

    def readline(self, length=None):
        if self.closed:
            raise ValueError, "I/O operation on closed file"
        if length is not None:
            r = self.buf.readline(length)
        else:
            r = self.buf.readline(length)
        self.pos = self.buf.tell()
        return r

    def readlines(self):
        if self.closed:
            raise ValueError, "I/O operation on closed file"
        lines = self.buf.readlines()
        self.pos = self.buf.tell()
        return lines

    def truncate(self, size=None):
        if self.closed:
            raise ValueError, "I/O operation on closed file"
        self.buf.truncate(size)
        self.pos = self.buf.tell()
        self.buf.seek(0, 2)
        self.len = self.buf.tell()
        self.buf.seek(self.pos)

    def write(self, s):
        if self.closed:
            raise ValueError, "I/O operation on closed file"
        self.buf.write(s)
        self.pos = self.buf.tell()
        self.buf.seek(0, 2)
        self.len = self.buf.tell()
        self.buf.seek(self.pos)

    def writelines(self, lines):
        if self.closed:
            raise ValueError, "I/O operation on closed file"
        self.buf.writelines(lines)
        self.pos = self.buf.tell()
        self.buf.seek(0, 2)
        self.len = self.buf.tell()
        self.buf.seek(self.pos)

    def flush(self):
        if self.closed:
            raise ValueError, "I/O operation on closed file"
        self.buf.flush()

    def getvalue(self):
        return self.buf.getvalue()

