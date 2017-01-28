#!/usr/bin/env python
#
# dtrace-controller  Schedules distributed test and observe regimens. 
#
#
# Copyright 2017 Ben Hadley 
# Licensed under the MIT License (the "License")
#
# 27-Jan-2017    Ben Hadley   Created this.


import logging
import signal
import sys
import warnings
from argparse import ArgumentParser

from core.scheduler import Scheduler

# Suppress runtime warning for import statements in event modules.
# Imports of Python standard library packages do work, but a warning was given
# indicating that the parent module was not found.
# This warning may not appear if havoc is in sys.path
warnings.filterwarnings(
    'ignore', '.*not found while handling absolute import.*'
)

def main():
    schedulers = None # will reference a list of Scheduler instances 

    def exit_dtrace(signum, stack):
        """ shuts down all schedulers (running threads) and exits"""
        map(lambda s: s.stop(), schedulers)
        print
        sys.exit()

    arg_parser = get_arg_parser()
    args = arg_parser.parse_args()  # get CLI arguments
    config_logger(args.e, args.d) # configure Python logging facility
    signal.signal(signal.SIGINT, exit_dtrace) # register Interrupt signal
    signal.signal(signal.SIGTERM, exit_dtrace) # register Terminate signal
    signal.signal(signal.SIGHUP, exit_dtrace) # register Terminal HangUp
    signal.signal(signal.SIGALRM, exit_dtrace) # register alarm 
    
    try:
        # Instantiate a Scheduler instance for each config file given at CLI.
        schedulers = [Scheduler(f, args.r) for f in args.session_config_file]
    except IOError as err:
        # Failed to open a system config file.
        sys.stderr.write('%s: error: %s- %s\n\n' 
                         % (arg_parser.prog, err.strerror, err.filename))
        sys.exit(2) # exit with error - 2 for CLI syntax errors
    except ValueError as err:
        # Content error in system config file.
        sys.stderr.write('%s: error: %s- %s\n\n' 
                         % (arg_parser.prog, err.args[1], err.args[0]))
        sys.exit(1) # exit with error
    except ImportError as err:
        # Failed to load fault injector file.
        sys.stderr.write('%s: error: %s\n\n' % (arg_parser.prog, err.args[0]))
        sys.exit(1) # exit with error

    # Scheduler is derived from Thread.  This will start each Thread.
    map(lambda s: s.start(), schedulers)

    # Setup alarm for a fixed duration session if necessary.
    if args.time: signal.alarm(args.time)

    # All FaultSims (threads) are running, main thread now waits for OS signal.
    signal.pause()


def config_logger(export = False, debug = False):
    """ Setup logging environment 
        unix_time: true for unix timestamp format
        debug: true for debug level logging output"""
    class UnixTimeFormatter(logging.Formatter):
        def formatTime(self, record, datefmt = None):
            return "{0:10.0f}".format(record.created)

    format_ = None
    if export:
        # File export format
        format_ = UnixTimeFormatter('%(asctime)s|%(threadName)s|%(message)s')
    else:
        # Terminal output format.
        format_ = logging.Formatter(
            fmt = '[%(asctime)s] %(threadName)-40s > %(message)s',
            datefmt = "%Y-%m-%d %H:%M:%S"
        )

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(format_)
    logging.getLogger().setLevel(logging.DEBUG if debug else logging.INFO)
    logging.getLogger().addHandler(ch)


def get_arg_parser():
    """ returns: an ArgumentParser instance with CLI arguments and help
            information"""
    parser = ArgumentParser(
        usage = "dtest-controller.py [OPTION ...] FILE [FILE ...]",
        description = "DTest Controller - distributed test scheduler"
    )

    parser.add_argument(
        '-d', '--debug', action = 'store_true', default = False, 
        dest = 'd', help = "set logging level to debug output"
    )

    parser.add_argument(
        '-e', '--export', action = 'store_true', default = False,
        dest = 'e', help = "logging output will be in file export format"
    )

    parser.add_argument(
        '-r', '--dryrun', action = 'store_true', default = False, 
        dest = 'r', help = "scheduled events will be reported but not executed"
    )

    parser.add_argument(
        '-t', '--time', type = int, default = 0, 
        help = "session duration in seconds"
    )

    parser.add_argument(
        'session_config_file', nargs = '+', metavar = 'FILE',
        help = "configuration (JSON) file for the current session"
               " (when FILE is -, read standard input)"
    )

    return parser


if __name__ == '__main__':
    """ dtrace-controller entry point"""
    main()
