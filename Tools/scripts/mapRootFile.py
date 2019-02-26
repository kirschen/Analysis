#!/usr/bin/env python

""" Callable function for deepCheckRootFile
"""

# Standard Imports
import os, sys

# DeepCheck Imports
from Analysis.Tools.helpers import mapRootFile

if len(sys.argv) > 1:
    mapRootFile( sys.argv[1] )
