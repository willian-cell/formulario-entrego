import sys
import os

# Caminho do seu projeto no PythonAnywhere
path = '/home/Willian96w38528736/mysite'
if path not in sys.path:
    sys.path.insert(0, path)

from app import app as application
