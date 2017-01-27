"""

eventparser.py: This module provides key-value data parsing
facilities.  Event modules will have key-value attributes
in the docstrings of the event functions.  The purpose of these
attributes are twofold:  1) provide additional configuration
options for fault functions, and 2) provide a means to protect
against accidental execution of Python code which is not reg 
event functionality.

"""

import inspect
import re

# Event function attribute keys.
EXECUTE_KEY = 'execute'

def parse_fault(func):
    """ Extracts the key-value data found in the docstrings of
            event functions.  The expected structure will
            have the form:
                [fault]
                  execute = true
                [/fault]
            as an example.
        func: a callable Python object
        returns: a dictionary of all key-value pairs"""
    key_values = {}
    TAG_RE = re.compile(r"^\[\s*/?fault\s*\]$")
    KEY_VALUE_RE = re.compile(r"^(?P<key>\w+)\s*=\s*(?P<value>.*)$")

    # Extract the docstring.
    config = inspect.getdoc(func)
    if config is None:
        return key_values

    reading_faults = False # toggles when tag '[fault]' reached
    for lino, line in enumerate(config.splitlines(), start = 1):
        line = line.strip()

        if not line: continue

        if TAG_RE.match(line):
            # Found '[fault]' tag.
            if reading_faults: break # encountered '[/fault]' tag
            else: reading_faults = True

        if reading_faults:
            key_value = KEY_VALUE_RE.match(line)
            if key_value and reading_faults:
                 # Found a key-value pair.
                 key = key_value.group("key")
                 key_values[key] = key_value.group("value")

    return key_values
