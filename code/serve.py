"""
evoke app server script

this is for serving a single app

"""

import os
import sys
import imp

# fix the path
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(1, os.path.abspath('../..'))

from twisted.application import service

from base.serve import start

# Twisted requires the creation of the root-level application object
# to take place in this file.
application = service.Application("evoke application")

#  stitch it all together...
start(application)
