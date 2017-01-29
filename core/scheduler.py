"""

scheduler.py: This module contains the Scheduler class.  

A Scheduler instance is a thread of execution for activating
events associated with a single system under test (SUT).

"""

import imp
import logging
import threading
import time

from systemundertest import SystemUnderTest

# Subdirectory name for all event modules.
FAULT_PKG = 'event'

class Scheduler(threading.Thread):

    def __init__(self, sut_config_filename, dryrun = False):
        """ Create Scheduler object.
            sut_config_filename: filename for the JSON configuration
                file associated with the system under test
            dryrun: if True, the event logic will not execute"""
        self._sut = SystemUnderTest(sut_config_filename)

        threading.Thread.__init__(
            self, name = "%s" % self._sut.get_system_name()
        )

        self._dryrun = dryrun
        self._fault_module_name = self._sut.get_fault_module_name()
        self._stop = threading.Event()
        self._function_cache = {} # cache of callable objects (faults)
        try:
            # Load the fault injector module
            self._fault_module = self.get_fault_module()
        except ImportError as err:
            raise ImportError(
                "Fault injector module '%s' could not be interpreted: %s" 
                % (self._fault_module_name, err)
            ) 


    def run(self):
        """ Entry point for threading.Thread (primary Scheduler thread)"""
        jobs = [] # holds currently running worker threads
        logging.info('Running')

        while True:
            # Build list of worker threads that are still alive.
            jobs = [job for job in jobs if job.is_alive()]

            if self._stop.isSet():
                # Wait for all running worker threads to finish if
                # we received a shutdown signal.
                logging.info('Stopping ...')
                for job in jobs:
                    job.join() 
                return

            # Execute a checkpoint on the system under test and iterate
            # through all active events.
            for e in self._sut.checkpoint():
                # Get the fault injector callable object for the active event.
                fault = None
                try:
                    fault = self.get_function(e.get_fault())
                except AttributeError as err:
                    # Could not find the function in fault injector module.
                    logging.info("error: %s- %s" % (
                        self._fault_module_name, err.args[0])
                    )
                    continue

                if self._dryrun:
                    # CLI argument indicated a simulation run.
                    logging.info("Dry run: %s (target:%s)" % (fault.__name__, 
                                  e.select_component_target()))
                else:
                    # Launch a worker thread to run a fault injection call.
                    p = threading.Thread(
                        name = "%s-%s" % (self._fault_module_name,
                                          fault.__name__),
                        target = self.worker, args = (fault, e)
                    )
                    jobs.append(p) # add to list of active worker threads
                    p.start()

            time.sleep(1) # sleep for 1 second between checkpoints
            # End of infinite loop. 


    def stop(self):
        """ Initiate shutdown of the Scheduler.  All active worker threads
            running fault injection tasks will complete."""
        self._stop.set()


    def worker(self, func, args):
        """ Entry point for a worker thread running a fault injection task.
            func: a callable function object from a fault injector module
            args: will contain the active Event instance
            """
        logging.debug("Starting %s (id:%s) fault simulation" 
                     % (func.__name__, args.get_component_id()))

        func(target = args.select_component_target(), 
             udf1 = args.get_user_def_field_1(),
             udf2 = args.get_user_def_field_2(),
             udf3 = args.get_user_def_field_3(),
             udd = args.get_user_def_dictionary())

        logging.debug("Completed %s (id:%s) fault simulation"
                     % (func.__name__, args.get_component_id()))
        return


    def get_fault_module(self):
        """ Loads the executable code from a fault injector module.
            returns: fault injector module"""
        if not isinstance(self._fault_module_name, basestring):
            raise ValueError("Invalid fault module name type '%s'"
                             % self._fault_module_name)

        f, f_name, desc = imp.find_module(self._fault_module_name, [FAULT_PKG])

        try:
            fault_module = imp.load_module(f_name, f, 
                                           self._fault_module_name, desc)
        finally:
            if f: f.close()

        return fault_module


    def get_function(self, func_name):
        """ Retrieves the fault injector function.
            func_name: name of the function
            returns: a callable function"""
        func = self._function_cache.get(func_name, None)

        if func is None:
            func = getattr(self._fault_module, func_name)
            if not hasattr(func, "__call__"):
                raise AttributeError()
            self._function_cache[func_name] = func

        return func
