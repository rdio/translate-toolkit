#!/usr/bin/env python
try:
  import translate
except ImportError:
  import sys
  import os
  translatepath=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
  sys.path.append(translatepath)

