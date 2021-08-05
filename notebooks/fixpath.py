import sys
import os

parentdir = os.path.dirname(os.getcwd())
if parentdir not in sys.path:
    sys.path.insert(0, parentdir)
