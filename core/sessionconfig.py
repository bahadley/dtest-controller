"""

sessionconfig.py:  This module is responsible for
all interactions with the system under test configuration
files.  The contents of these files are JSON text.
They specify the event module for the system,
all components of the system, and the activation/probability
model for the compenents.

SessionConfig:  This class implements all the logic
for the responsibilities described above.  The class
also handles all validation of the configuration file
contents.

"""

from collections import namedtuple
# Ideally we would use simplejson, but is it available
# on every Python 2.7.x installation?
# import simplejson as json
import json
import os
import sys

# JSON config file key names.
SYSTEM_NAME = 'system_name'
FAULT_MODULE = 'fault_module'
COMPONENTS = 'components'
COMPONENT_ID = 'id'
COMPONENT_ACTIVE = 'active'  # [true|false] component ignored if false
COMPONENT_TARGETS = 'targets'
OPERABLE_EVENTS = 'operable_events'
NONOPERABLE_EVENTS = 'nonoperable_events'

EVENT_ID = 'id'
EVENT_INSTANCES = 'instances' # the number of event instances to be created
EVENT_FAULT = 'fault'
EVENT_STATE_TRANS = 'state_transition' # [true|false] event causes a state
                                       # transition of the SystemComponent
EVENT_ACTIVATION_MODEL = 'a_model'
EVENT_PROB_MODEL = 'p_model' # not required for fixed activation model
EVENT_MTTF = 'mttf' # required for all probability models except random
EVENT_THRESHOLD = 'threshold' # minimum wait time before event occurs
EVENT_EFF_START = 'effective_start' # optionally used to sequence events
EVENT_EFF_END = 'effective_end' # optionally used to sequence events
EVENT_RAND_RANGE = 'random_range' # for random probability model
EVENT_RAND_W_TYPE = 'random_window_type' # for random probability model
EVENT_ST_DEV = 'standard_deviation' # only for normal probability model
EVENT_SHAPE = 'shape' # only for weibull probability model
EVENT_UDF1 = 'udf1' # optional user defined field
EVENT_UDF2 = 'udf2' # optional user defined field
EVENT_UDF3 = 'udf3' # optional user defined field
EVENT_UDD = 'udd' # optional user defined field as dictionary


class SessionConfig(object):

    # All possible activation models.
    EVENT_AMOD_RECUR = 'recurring'
    EVENT_AMOD_SINGLE = 'singular'

    # All possible probability models.
    EVENT_PMOD_EXP = 'exponential' # hazard rate function
    EVENT_PMOD_NORM = 'normal' # hazard rate function
    EVENT_PMOD_WEI = 'weibull' # hazard rate function
    EVENT_PMOD_RANDOM = 'random' # uniformly distributed probability
    EVENT_PMOD_DETER = 'deterministic' # no random variable 

    # All possible random probability model windows.
    EVENT_RAND_SLIDE = 'sliding'
    EVENT_RAND_FIXED = 'fixed'

    def __init__(self, session_config_file):
        """ Create SessionConfig object.
            session_config_file: name of the configuration file"""
        self._file_name = session_config_file
        self._json_data = None

        f = None
        if session_config_file is '-':
            f = sys.stdin
        else:
            f = open(session_config_file)

        try:
            self._json_data = json.load(f)
        except ValueError as err:
            # With simplejson, err will have more detailed error
            # info.  Also, it has the JSONDecodeError class.
            # But can be count on simplejson being installed?
            # We want to avoid extra dependencies.
            raise ValueError(err, self._file_name)
        finally:
            if session_config_file is not '-': f.close()


    def get_system_name(self):
        """ returns: name of the system under test"""
        try:
            return self._json_data[SYSTEM_NAME]
        except KeyError:
            raise ValueError("Missing '%s' value" % SYSTEM_NAME,
                             self._file_name)


    def get_fault_module_name(self):
        """ returns: name of the fault injector module for the system"""
        fault_module_name = None
        try:
            s = self._json_data[FAULT_MODULE]
            if not isinstance(s, basestring):
                raise ValueError("Invalid fault module name type '%s'"
                                 % s, self._file_name)
            fault_module_name = s[:-3] if s.endswith('.py') else s 
        except KeyError:
            raise ValueError("Missing '%s' value" % FAULT_MODULE,
                             self._file_name)

        return fault_module_name


    def get_active_components(self):
        """ returns: list of component tuples (id, list of targets) 
                     which are marked as active"""
        components = list() # list of tuples: (id, list of targets)
        try:
            for c in self._json_data[COMPONENTS]:
                if COMPONENT_ID not in c:
                    raise ValueError("Missing '%s' value in '%s' List"
                                     % (COMPONENT_ID, COMPONENTS), 
                                     self._file_name)
                if COMPONENT_TARGETS not in c:
                    raise ValueError("Missing '%s' value in '%s' List"
                                     % (COMPONENT_TARGETS, COMPONENTS), 
                                     self._file_name)
                if not isinstance(c[COMPONENT_TARGETS], list):
                    raise ValueError("'%s' must be mapped to type List" 
                                     % COMPONENT_TARGETS, self._file_name)
                if COMPONENT_ACTIVE not in c:
                    raise ValueError("Missing '%s' value in '%s' List"
                                     % (COMPONENT_ACTIVE, COMPONENTS), 
                                     self._file_name)
                if type(c[COMPONENT_ACTIVE]) is not bool:
                    raise ValueError("Invalid '%s' data type" 
                                     % COMPONENT_ACTIVE, 
                                     self._file_name)
                
                if c[COMPONENT_ACTIVE]: 
                    c_id = c[COMPONENT_ID]
                    c_targets = c[COMPONENT_TARGETS]

                    if not c_targets:
                        raise ValueError("Invalid '%s' value (empty List)" 
                                         % COMPONENT_TARGETS, self._file_name) 

                    components.append((c_id, c_targets)) 

        except KeyError:
            if COMPONENTS not in self._json_data:
                raise ValueError("Missing '%s' value" % COMPONENTS,
                                 self._file_name)
        except TypeError:
            raise ValueError("'%s' must be mapped to List" % COMPONENTS,
                             self._file_name)

        return components


    def get_events_for_component(self, component_id, operable = True):
        """ component_id: id of a component
            operable: true to retrieve list of operable events;
                      false for nonoperable events
            returns list of event tuples (id, # of instances)
                    for the component and operable state"""
        events = list() # list of tuples: (id, # of instances)
        event_type = OPERABLE_EVENTS if operable else NONOPERABLE_EVENTS 

        for c in self._json_data[COMPONENTS]:
            try:
                if (c[COMPONENT_ID] == component_id and event_type in c):
                    for e in c[event_type]:
                        event_id = e[EVENT_ID]
                        instances = (e[EVENT_INSTANCES] 
                                     if EVENT_INSTANCES in e
                                     else 1)

                        if type(instances) is not int or instances < 0:
                            raise ValueError("Invalid '%s' value" 
                                             % EVENT_INSTANCES, 
                                             self._file_name) 

                        events.append((event_id, instances))
                    
            except KeyError:
                raise ValueError("Missing '%s' value for event" % EVENT_ID,
                                 self._file_name)
            except TypeError:
                raise ValueError("Events must be mapped to dictionary",
                                 self._file_name)

        return events


    def get_model_for_event(self, component_id, event_id):
        """ component_id: id of a component
            event_id: id of an event configured for the component
            returns: a namedtuple instance with all activation/probability
                attributes for the event"""
        ModelType = namedtuple(
            'ModelType', 
            'fault state_trans a_model p_model mttf thrld eff_s eff_e sd'
            ' shape r_range r_w_type udf1 udf2 udf3 udd'
        )

        e = self._get_event_config_for_component(component_id, event_id)

        if not isinstance(e, dict):
            raise ValueError("Event must be mapped to type Dictionary", 
                             self._file_name)

        if EVENT_FAULT not in e:
            raise ValueError("Missing '%s' value for event %s" % 
                             (EVENT_FAULT, event_id),
                              self._file_name)

        if EVENT_ACTIVATION_MODEL not in e:
            raise ValueError("Missing '%s' value for event %s" % 
                             (EVENT_ACTIVATION_MODEL, event_id),
                              self._file_name)

        event = ModelType(e[EVENT_FAULT],
                          e[EVENT_STATE_TRANS] if EVENT_STATE_TRANS in e
                                               else False,
                          e[EVENT_ACTIVATION_MODEL], 
                          e[EVENT_PROB_MODEL] if EVENT_PROB_MODEL in e else '',
                          e[EVENT_MTTF] if EVENT_MTTF in e else 1,
                          e[EVENT_THRESHOLD] if EVENT_THRESHOLD in e else 0,
                          e[EVENT_EFF_START] if EVENT_EFF_START in e else -1,
                          e[EVENT_EFF_END] if EVENT_EFF_END in e else -1,
                          e[EVENT_ST_DEV] if EVENT_ST_DEV in e else 1,
                          e[EVENT_SHAPE] if EVENT_SHAPE in e else 1,
                          e[EVENT_RAND_RANGE] if EVENT_RAND_RANGE in e else 1,
                          e[EVENT_RAND_W_TYPE] if EVENT_RAND_W_TYPE in e 
                              else self.EVENT_RAND_FIXED,
                          e[EVENT_UDF1] if EVENT_UDF1 in e else '',
                          e[EVENT_UDF2] if EVENT_UDF2 in e else '',
                          e[EVENT_UDF3] if EVENT_UDF3 in e else '',
                          e[EVENT_UDD] if EVENT_UDD in e else None)

        # Validate model
        self._validate_event_model(event)

        return event


    def _get_event_config_for_component(self, component_id, event_id):
        """ component_id: id of a component
            event_id: id of an event configured for the component
            returns: a dictionary instance with all activation/probability
                attributes for the event as read directly from JSON file"""
        for c in self._json_data[COMPONENTS]:
            if c[COMPONENT_ID] == component_id:
                for e in c[OPERABLE_EVENTS]:
                    if (e[EVENT_ID] == event_id): return e
                for e in c[NONOPERABLE_EVENTS]:
                    if (e[EVENT_ID] == event_id): return e


    def _validate_event_model(self, e):
        """ Validates all activation/probability attributes for the event.  A
                ValueError exception will be thrown for any invalid attribute.
            e: ModelType namedtuple with event attributes"""
        # Validate state_trans value
        if type(e.state_trans) is not bool: 
            raise ValueError("Invalid '%s' data type" % EVENT_STATE_TRANS, 
                             self._file_name)

        # Validate activation model value
        if not (e.a_model == self.EVENT_AMOD_RECUR or 
            e.a_model == self.EVENT_AMOD_SINGLE):
            raise ValueError("Invalid %s value '%s'" % 
                             (EVENT_ACTIVATION_MODEL, e.a_model),
                             self._file_name)

        # Validate probability model value
        if not (e.p_model == self.EVENT_PMOD_EXP or
            e.p_model == self.EVENT_PMOD_NORM or
            e.p_model == self.EVENT_PMOD_WEI or
            e.p_model == self.EVENT_PMOD_RANDOM or
            e.p_model == self.EVENT_PMOD_DETER):
            raise ValueError("Invalid %s value '%s'" % 
                             (EVENT_PROB_MODEL, e.p_model),
                             self._file_name)

        # Validate random window value
        if not (e.r_w_type == self.EVENT_RAND_SLIDE or 
            e.r_w_type == self.EVENT_RAND_FIXED):
            raise ValueError("Invalid %s value '%s'" % 
                             (EVENT_RAND_W_TYPE, e.r_w_type),
                             self._file_name)

        # Validate mttf
        if type(e.mttf) is not int or e.mttf <= 0:
            raise ValueError("Invalid %s value '%s'" %
                             (EVENT_MTTF, e.mttf),
                              self._file_name) 

        # Validate threshold
        if type(e.thrld) is not int or e.thrld < 0:
            raise ValueError("Invalid %s value '%s'" %
                             (EVENT_THRESHOLD, e.thrld),
                              self._file_name) 

        # Validate effective_start 
        if type(e.eff_s) is not int or e.eff_s < -1:
            raise ValueError("Invalid %s value '%s'" %
                             (EVENT_EFF_START, e.eff_s),
                              self._file_name) 

        # Validate effective_end 
        if type(e.eff_e) is not int or e.eff_e < -1:
            raise ValueError("Invalid %s value '%s'" %
                             (EVENT_EFF_END, e.eff_e),
                              self._file_name) 

        # Validate standard deviation
        if type(e.sd) is not int or e.sd <= 0:
            raise ValueError("Invalid %s value '%s'" %
                             (EVENT_ST_DEV, e.sd),
                              self._file_name) 

        # Validate shape
        if type(e.shape) not in (float, int) or e.shape <= 0:
            raise ValueError("Invalid %s value '%s'" %
                             (EVENT_SHAPE, e.shape),
                              self._file_name) 

        # Validate random range 
        if type(e.r_range) is not int or e.r_range <= 0:
            raise ValueError("Invalid %s value '%s'" %
                             (EVENT_RAND_RANGE, e.r_range),
                              self._file_name) 
