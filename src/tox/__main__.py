"""
Automatically package and test a Python project against configurable
Python2 and Python3 based virtual environments. Environments are
setup by using virtualenv. Configuration is generally done through an
INI-style "tox.ini" file.
"""
from .commands import cmdline

if __name__ == "__main__":
    cmdline()
