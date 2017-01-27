"""

systemundertest.py: Contains the SystemUnderTest class.

A SystemUnderTest instance is an abstraction of an actual computing 
system.  For instance, a system may be the Open Stack compute
service (nova), or it may be the Linux networking stack, or a software
application.  A SystemUnderTest instance will be mapped to a single
fault injection module.
 
"""

from systemcomponent import SystemComponent
from sessionconfig import SessionConfig

class SystemUnderTest(object):

    def __init__(self, session_config_file):
        """ Create SystemUnderTest object.
            system_config_file: name of the configuration file;
                used to create the full path name of the file"""
        self._config_file = SessionConfig(session_config_file)
        self._system_name = self._config_file.get_system_name()
        self._fault_module_name = self._config_file.get_fault_module_name()
        self._components = [
            SystemComponent(c[0], c[1], self._config_file) for 
            c in self._config_file.get_active_components()
        ]


    def checkpoint(self):
        """ Determines whether any events associated with components need
                to be activated.
            returns: list of Event instances which are active"""
        events = []

        for c in self._components:
            active_events = c.checkpoint()
            if active_events: events.extend(active_events)

        return events


    def get_system_name(self):
        """ returns: name of system under test (SUT)"""
        return self._system_name


    def get_fault_module_name(self):
        """ returns: name of fault injector module associated with the SUT"""
        return self._fault_module_name
