"""
Autoguess - Automated guess-and-determine and key-bridging attacks
on symmetric-key cryptographic primitives.

Copyright (C) 2021 Hosein Hadipour
License: GPL-3.0-or-later
"""

try:
    from importlib.metadata import version as _version
    __version__ = _version("autoguess")
except Exception:
    __version__ = "1.0.0"
