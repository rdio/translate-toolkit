#!/usr/bin/python2.2

from distutils.core import setup, Extension

csvModule = Extension('_csv', ['_csv.c'])

setup(name="_csv",version="2.3b",description="csv module",py_modules=['csv'],ext_modules=[csvModule])

