#!/usr/bin/env python

"""manages projects and files and translations"""

import re
import os
import popen2

def pipe(command):
  """runs a command and returns the output and the error as a tuple"""
  # p = subprocess.Popen(command, shell=True, close_fds=True,
  #   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  p = popen2.Popen3(command, True)
  (c_stdin, c_stdout, c_stderr) = (p.tochild, p.fromchild, p.childerr)
  output = c_stdout.read()
  error = c_stderr.read()
  ret = p.wait()
  c_stdout.close()
  c_stderr.close()
  c_stdin.close()
  return output, error

def cvsreadfile(cvsroot, path, revision=None):
  """
  Read a single file from the CVS repository without checking out a full working directory
  
  cvsroot: the CVSROOT for the repository
  path: path to the file relative to cvs root
  revision: revision or tag to get (retrieves from HEAD if None)
  """
  
  # Shell-escape any non-alphanumeric characters
  path = re.sub(r'(\W)', r'\\\1', path)
  
  if revision:
    command = "cvs -d %s -Q co -p -r%s %s" % (cvsroot, revision, path)
  else:
    command = "cvs -d %s -Q co -p %s" % (cvsroot, path)

  output, error = pipe(command)

  if error.startswith('cvs checkout'):
    raise IOError("Could not read %s from %s: %s" % (path, cvsroot, output))
  elif error.startswith('cvs [checkout aborted]'):
    raise IOError("Could not read %s from %s: %s" % (path, cvsroot, output))

  return output

def svnreadfile(path, revision=None):
  """Get a clean version of a file from the CVS repository"""
  path = re.sub(r'(\W)', r'\\\1', path)
  if revision:
    command = "svn cat -r %s %s" % (revision, path)
  else:
    command = "svn cat %s" % path
  output, error = pipe(command)
  if error:
    raise IOError("Subversion error: %s" % error)
  return output

def getcleanfile(filename, revision=None):
  parentdir = os.path.dirname(filename)
  cvsdir = os.path.join(parentdir, "CVS")
  if os.path.isdir(cvsdir):
    cvsroot = open(os.path.join(cvsdir, "Root"), "r").read().strip()
    cvspath = open(os.path.join(cvsdir, "Repository"), "r").read().strip()
    cvsfilename = os.path.join(cvspath, os.path.basename(filename))
    return cvsreadfile(cvsroot, cvsfilename)
  svndir = os.path.join(parentdir, ".svn")
  if os.path.isdir(svndir):
    return svnreadfile(filename, revision)
  raise IOError("Could not find version control information")

if __name__ == "__main__":
  import sys
  filenames = sys.argv[1:]
  for filename in filenames:
    contents = getcleanfile(filename)
    sys.stdout.write(contents)

