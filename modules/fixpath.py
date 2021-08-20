import sys
import os

parentdir = os.path.dirname(os.getcwd())
submodules_dir = parentdir + '/submodules/ludopedia_wrapper'

if submodules_dir not in sys.path:
    sys.path.insert(0, submodules_dir)
