"""

systemcomponent.py: Contains the SystemComponent class.

Each SystemUnderTest has one or more SystemComponent instances.  These 
instances may correspond to running virtual machine instances, in the 
case Open Stack compute, or to a vSwitch instance or veth pair in the 
case of the Linux networking stack.  The 'target' attribute will be used 
to uniquely identify the component within the fault injector code.  A 
SystemComponent instance is a simple state machine.  There are two possible 
states: Operable and Nonoperable.  A SystemComponent will transition 
between states only when a 'state_transition' event is activated.  By 
default, events are not configured as 'state_transition'.  A SystemComponent 
will always remain in the Operable state when all the events assigned to 
it are not 'state_transition' events. 

"""

from time import time

from event import Event

class SystemComponent(object):

    # SystemComponent instances have the following possible states.
    OPERABLE = True
    NONOPERABLE = False

    def __init__(self, component_id, targets, config):
        """ Create SystemComponent object.
            component_id: id of the component
            targets: a list of component identifiers which may be subject 
                   to faults.  Frequently, this will be a single entity, 
                   but it could be a list of identifiers such that one 
                   is randomly selected during event activation
            config: a SessionConfig instance"""
        self._id = component_id
        self._targets = targets
        self._state = self.OPERABLE
        self._events = {self.OPERABLE:[], self.NONOPERABLE:[]}
        # Time when the component was initialized.  Used for sequencing
        # events that have effective start and end times.
        self._life_start_time = time()
        # Time of the last event activation.  Used to determine the 
        # elapsed time since the previous event.  The time will mark the
        # moment when the event is initially activated.  The execution
        # duration of the associated fault function is indeterminant.
        self._last_event_time = time()

        for e in config.get_events_for_component(self._id):
            for _ in range(e[1]):
                # Append # of events corresponding to 'instance' parameter
                self._events[self.OPERABLE].append(
                                            Event(self._id, self._targets, 
                                                  e[0], config)
                                            )
        for e in config.get_events_for_component(self._id, False):
            for _ in range(e[1]):
                # Append # of events corresponding to 'instance' parameter
                self._events[self.NONOPERABLE].append(
                                               Event(self._id, self._targets, 
                                                     e[0], config)
                                               )


    def checkpoint(self):
        """ Determines whether any events associated with the component's
                state need to be activated.
            returns: list of Event instances which are active"""
        # Build list of activated events.
        active_events = [
            e for e in self._events[self._state] 
            if e.is_active(self._life_start_time, 
                           self._last_event_time)
        ]

        for e in active_events:
            e.set_executed()
            self._last_event_time = time()
            # Transition the component state if necessary.
            if e.is_state_transition_event(): 
                self._state = not self._state

        return active_events
