#!/usr/bin/env python
""""Initiation point for the query subsystem.

NetworkSearch2.manager is an initiation point for the system.
It will start the user interface component (used for web and others)
and start a query subsystem for receive an incoming request and perform
distributed execution across the system.

@author: Misbah Uddin

"""

import argparse
import logging
import sys

from NetworkSearch2.QuerySubsystem.dispatcher import IncomingDispatcher
from NetworkSearch2.QuerySubsystem.echoProcess import initializer
from NetworkSearch2.interface.interface import queryInterface
from NetworkSearch2.ProfileTools.myProfiler import Profiler

#below configuration for start/stop service
from NetworkSearch2.util.daemon import Daemon


def get_args():
    """ A function for getting command line arguments."""

    parser = argparse.ArgumentParser(description="Network Search module")
    parser.add_argument("-debug", action='store_true', default=False,
                        help='add debug level information to a log')
    parser.add_argument("-profile", action='store_true', default=False,
                        help='enable a profiling of the system.\
                              Note that you need to start \
                              NetworkSearch2/util/profileServer.py first')
    parser.add_argument("-no_interface", action='store_true', default=False,
                        help='In case of use load generator, we need to \
                              disable system interface \
                              and use load generator instead')
    parser.add_argument("mode", choices=['start', 'stop', 'restart'],
                        help='to start/stop/restart the Network Search module')
    return parser.parse_args()


class NetworkSearch(Daemon):
    """ A class for starting the Network search modules.
        (only interface and query subsystems) """

    def __init__(self, args, pidfile, stdin='/dev/null',
                 stdout='/dev/null', stderr='/dev/null'):
        super(NetworkSearch, self).__init__(pidfile, stdin, stdout, stderr)
        self.args = args

    def run(self):
        """Overwrite a Daemon class. This method will be called when
           the daemon started"""

        # Logging
        logging.info("=" * 20)
        logging.info("Network Search module stated ")
        logging.info("=" * 20)

        # Initialize an Echo process service and return
        # a list of queue use to receive a query.
        queue_list = initializer()

        # Initialize a dispatcher service.
        # This service will be an first point of contact for all requests.
        IncomingDispatcher(queue_list).start()

        # Initialize a interface process service -
        # an interface through which the user interact.
        if not self.args.no_interface:
            queryInterface().start()

        logging.info("End of initiation phase")


def main():

    # Read command arguments
    try:
        args = get_args()
    except IOError as(errno, strerror):
        print "IOError({0}): {1}".format(errno, strerror)

    # Setup a logging
    logging_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
                filename=str(sys.path[0]) + '/NetworkSearch2.log',
                level=logging_level,
                format='%(asctime)s %(levelname)s: %(module)s: %(message)s',
                datefmt='%m/%d/%Y %I:%M:%S %p')

    # Setup profiler
    Profiler.enabled = args.profile

    # Setup a daemon
    daemon = NetworkSearch(args, '/tmp/NetworkSearch2.pid',
                           stdout=sys.stdout, stderr='NetworkSearch2.log')
    if 'start' == args.mode:
        print 'started'
        daemon.start()
    elif 'stop' == args.mode:
        manualkill()
        daemon.stop()
        print 'stopped'
    elif 'restart' == args.mode:
        manualkill()
        daemon.restart()
    else:
        pass


def manualkill():
    """ a function for kill processes.

    Since the system can create sub-processes,
    if we want to close, we need to kill all relevant processes too.
    (Amy's code)

    """

    # Name of the process that is running (irrelevant of where it was started)
    from subprocess import Popen, PIPE
    from signal import SIGTERM
    import os
    name = sys.argv[0].split('/').pop()
    p1 = Popen(['ps', 'x'], stdout=PIPE)
    procs = Popen(['grep', 'python.*' + name],
                  stdin=p1.stdout, stdout=PIPE).communicate()[0]
    p1.stdout.close()
    for p in procs.splitlines():
        p_pid = int(p.split()[0])
        if p_pid != os.getpid() and p.split()[4] != 'grep':
            os.kill(p_pid, SIGTERM)

if __name__ == "__main__":
    exit(main())
