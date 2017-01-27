"""

Event.py: Contains the Event class.

Each SystemComponent will have one or more Event instances.  These
events map to a specific event function.  Some events can only
be activated when the component is in an Operable state and others can
only be activated when the component is in a Nonoperable state.  A
SystemComponent is initialized in an Operable state.  Most events will 
be configured for the Operable state.

"""

from random import choice
from random import randint
from time import time

from stochastic import exponential_hazard
from stochastic import normal_hazard
from stochastic import weibull_hazard
from sessionconfig import SessionConfig

class Event():

    def __init__(self, component_id, targets, event_id, config):
        """ Create Event object.
            component_id: id of the component which this Event instance
                          will be associated with
            targets: a list of component identifiers which may be subject 
                   to faults.  Frequently, this will be a single entity, 
                   but it could be a list of identifiers such that one 
                   is randomly selected during event activation
            event_id: the event id unique to the component
            config: reference to a SessionConfig object"""
        self._id = event_id
        self._component_id = component_id
        self._targets = targets
        self._executed = False 

        # Members used for random p_model
        self._random_time = 0 # computed activation time
        self._window_end = time() # time when next _random_time is computed 
        self._random_time_set = False # toggle to trigger new computation

        # event_config is a NamedTuple defined in 
        # SystemConfigFile.get_model_for_event().
        event_config = config.get_model_for_event(self._component_id, self._id)
        self._fault = event_config.fault
        self._state_trans = event_config.state_trans
        self._act_model = event_config.a_model # activation model
        self._prob_model = event_config.p_model # probability model
        self._mttf = event_config.mttf # mean time to failure
        self._threshold = event_config.thrld # min time before activation
        self._effective_start = event_config.eff_s # for sequenced events
        self._effective_end = event_config.eff_e # for sequenced events
        self._standard_deviation = event_config.sd # only for normal p_model
        self._shape = event_config.shape # used only for weibull prob_model
        self._random_range = event_config.r_range # only for random p_model
        self._random_w_type = event_config.r_w_type # only for random p_model
        # The user defined fields are used to pass data which used in a 
        # unique manner by the fault function.
        self._udf1 = event_config.udf1
        self._udf2 = event_config.udf2
        self._udf3 = event_config.udf3
        self._udd = event_config.udd


    def get_component_id(self):
        """ returns: component id associated with this event"""
        return self._component_id


    def select_component_target(self):
        """ returns: target which will be activated"""
        return choice(self._targets)


    def get_fault(self):
        """ returns: fault name which corresponds to a fault module function"""
        return self._fault


    def get_activation_type(self):
        """ returns: activation model of event"""
        return self._act_model


    def get_user_def_field_1(self):
        """ returns: user defined type 1"""
        return self._udf1


    def get_user_def_field_2(self):
        """ returns: user defined type 2"""
        return self._udf2


    def get_user_def_field_3(self):
        """ returns: user defined type 3"""
        return self._udf3


    def get_user_def_dictionary(self):
        """ returns: user defined type organized as a dictionary"""
        return self._udd


    def set_executed(self):
        """ marks the event as having been executed"""
        self._executed = True


    def is_state_transition_event(self):
        """ returns: true if this event should transition the state of
                the component (ie. operable versus nonoperable);
                false if otherwise"""
        return self._state_trans

    def is_singular_event(self):
        """ returns: true if this event should only be executed once
                (ie. singular activation model);
                false if otherwise"""
        return (self._act_model == SessionConfig.EVENT_AMOD_SINGLE)


    def is_active(self, alive_time, last_event_time):
        """ Determines if this event is now activated based upon the
                model and the current time.
            alive_time: initialization time of the component.
            last_event_time: time when the previous event occurred
                or the component initialization time.
            returns: return true if the event is activated; false if not"""
        # Event with 'singular' activation models will only be
        # executed once
        if self._executed and self.is_singular_event(): return False

        # Get the elapsed time from when the component was initialized.
        elapsed_life = time() - alive_time
        # Get the elapsed time from either when the last event occurred
        # or when the component started up.
        elapsed_time = time() - last_event_time

        effective = True # supports sequenced events with effective times
        active = False # is the event now active based upon model

        if self._effective_start > -1:
            # Is the event in effect now? 
            if not (elapsed_life >= self._effective_start and 
                 (self._effective_end == -1 or 
                     elapsed_life <= self._effective_end)):
                effective = False

        if effective and elapsed_time >= self._threshold:
            # Is the event active now?
            if self._prob_model == SessionConfig.EVENT_PMOD_DETER:
                active = True
            elif self._prob_model == SessionConfig.EVENT_PMOD_EXP:
                active = exponential_hazard(self._mttf)
            elif self._prob_model == SessionConfig.EVENT_PMOD_NORM:
                active = normal_hazard(self._mttf,
                                    self._standard_deviation,
                                    elapsed_time)
            elif self._prob_model == SessionConfig.EVENT_PMOD_WEI:
                active = weibull_hazard(self._shape,
                                     self._mttf,
                                     elapsed_time)
            elif self._prob_model == SessionConfig.EVENT_PMOD_RANDOM:
                # This model precalculates when the event is to occur
                # and uses _random_time_set to toggle the set/unset state.
                current_time = time()
                if (not self._random_time_set and 
                        current_time > self._window_end):
                    # Compute the time in the future when the event will 
                    # next activate.
                    self._random_time = (self._window_end + 
                        randint(self._threshold, self._random_range))
                    # Compute the next window end
                    if (self._random_w_type == 
                            SystemConfigFile.EVENT_RAND_FIXED):
                        self._window_end = time() + self._random_range
                    else:
                        # Sliding Window.
                        self._window_end = self._random_time
                    self._random_time_set = True
                elif (self._random_time_set and 
                          current_time >= self._random_time):
                    self._random_time_set = False
                    active = True

        return active
