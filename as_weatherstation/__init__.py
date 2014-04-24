# We include third-party packages in ../lib/site-packages/
# We do this so users don't have to install a bunch of dependencies.
# To get those packages to play nice in that sub-directory
# we tell Python that the whole application is a site directory.
# The call to site.addsitedir() causes .pth files in ../ to be loaded.
# We have one called app.pth which specifies lib/site-packages.
# This causes the site module to then adds ../lib/site-packages/
# to the site.path variable which is used when trying to import modules.
#
# Convoluted? A bit. But I did that rather than just appending
# to site.path here as it seems more dynamic, and I like dynamic.
# 
# The short of this is that whenever any file in the as_weatherstation
# package is imported, all subsequent code will be able to import
# modules from lib/site-packages/ wihout issue and as if the module
# was installed in one of the default Python site-package locations.
#
# If a user wants to install third-party modules in the defaule locations
# instead, they can jsut remove those packages from ../lib/site-packages/
# and the application shouldn't skip a beat.
import site, os
site.addsitedir(os.getcwd())

"""
import sys
from pprint import pprint
pprint(sys.path)
"""
