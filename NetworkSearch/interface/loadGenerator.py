""" Load Generator sit in place of query interface,
and serve for a performance testing purpose.

@author: Misbah Uddin

"""

import argparse
import logging
import threading
import random
import sys
import time
from math import log

import zmq

from NetworkSearch2.QuerySubsystem.echoMessage import ECHOMessage
from NetworkSearch2.interpreter.nsInterfaceAlpha import nsInterface
from NetworkSearch2.QuerySubsystem.queryObject import QueryObject
from NetworkSearch2.ProfileTools.myProfiler import Profiler
#below configuration for start/stop service
from NetworkSearch2.util.daemon import Daemon

#############################
# read a configuration file #
#############################
from ConfigParser import SafeConfigParser
from sys import path

confparser = SafeConfigParser()
confparser.read([str(path[0]) + '/../config.cfg'])

# get values
INTERFACE_PORT = confparser.getint('Interface', 'interface_port')
DISPATCHER_PORT = confparser.getint('Dispatcher', 'dispatcher_port')
START_QID = confparser.getint('Interface', 'start_qid')

#############################


def get_args():
    parser = argparse.ArgumentParser(description="A load generator using \
                                     Poisson process.")
    parser.add_argument("mode", choices=['start', 'stop', 'restart'],
                        help='to start/stop/restart the Network Search module')
    parser.add_argument("-profile", action='store_true', default=False,
                        help='enable detail profile & disable global profile')
    parser.add_argument('queryListFile', type=argparse.FileType('r'),
                        default=None, help='A file contains list of queries \
                        to inject'
                        )
    parser.add_argument('-userExact', action='store_true', default=False,
                        help='force an exact result returned')
    parser.add_argument('-limit', type=int, default=None,
                        help='number of result returned')
    parser.add_argument('-rate', type=float, default=1.0,
                        help='Poisson arrival rate')
    parser.add_argument('-time', type=int, default=120,
                        help='the load generator will run for <time> seconds')

    return parser.parse_args()


class LoadGenerator(Daemon):

    def __init__(self, args, pidfile, stdin='/dev/null',
                stdout='/dev/null', stderr='/dev/null'):
        super(LoadGenerator, self).__init__(pidfile, stdin, stdout, stderr)

        # Init variables
        self.time_of_queries = {}
        self.args = args
        self.qid = START_QID

    def interpret(self, raw_query):
        """ (str,) -> Query_object
        Interpret the raw query to a query object so that
        the system can handle it.
        """

        # Parse the query
        match_query, project_query, aggr_query, \
        group_query, pass_one_query, link_attributes, \
        pass_two_query, flags = nsInterface(raw_query, self.args.userExact)

        if not match_query:
            logging.warning("unable to parse %s" % raw_query)

        if 'projection' in flags:
            project_query.update({'object-name': 1, 'object-type': 1})
            return QueryObject(
                     match_query, project_query,
                     parameters={'isRank': False, "isApprox": False,
                                 "limit": self.args.limit}
                     )
        elif 'aggregation' in flags:
            return QueryObject(
                     match_query, project_query,
                     aggr_query, group_query,
                     parameters={'isRank': False, "isApprox": False,
                                 "limit": self.args.limit}
                     )
        elif 'approximate' in flags:
            return QueryObject(
                     match_query,
                     parameters={'isRank': True, "isApprox": True,
                                 "limit": self.args.limit}
                     )
        elif 'exact' in flags:
            return QueryObject(
                     match_query,
                     parameters={'isRank': False, "isApprox": False,
                                 "limit": self.args.limit}
                     )

    def read_file_to_query_list(self, f):
        """ Read a line from a file and parse user queries into a list"""
        temp = []
        for line in f:
            raw_query = line.strip("\n")
            try:
                query = self.interpret(raw_query)
            except TypeError:
                print " '{}' can't parse properly".format(raw_query)
                continue
            temp.append(query)

        return temp

    def receive_thread(self):
        """ a thread for getting the result message from the system."""
        # Assign variable locally
        receiver = self.receiver
        time_of_queries = self.time_of_queries

        while 1:
            results = receiver.recv()
            msg = ECHOMessage.deserialize(results)

            # Logging results
            logging.info(time.time() - time_of_queries[msg.get_id()])

    def run(self):
        logging.basicConfig(
                    filename=str(path[0]) + '/../stats_' +
                             str(self.args.rate) + '.log',
                    level=logging.DEBUG, format='%(message)s')
        logging.info("=========execution start with poisson arrival rate \
                     {0} query per sec==========".format(self.args.rate))

        # Setup connection
        context = zmq.Context()
        self.receiver = context.socket(zmq.PULL)
        self.receiver.bind("tcp://*:{}".format(INTERFACE_PORT))
        self.sender = context.socket(zmq.PUSH)
        self.sender.connect("tcp://localhost:{}".format(DISPATCHER_PORT))

        # Start receiving thread
        t = threading.Thread(target=self.receive_thread)
        t.daemon = True
        t.start()

        # Load queries, (time consuming)
        print "loading queries..."
        queries = self.read_file_to_query_list(self.args.queryListFile)
        queries_pool_size = len(queries) - 1
        print "loading queries... completed"

        # Assign variable locally
        start_time = time.time()
        duration = self.args.time
        rate = self.args.rate
        sender = self.sender
        time_of_queries = self.time_of_queries

        print "=======start load generator======"

        while (time.time() - start_time) < duration:
            t0 = time.time()

            # Randomly pick a query
            query = queries[random.randint(0, queries_pool_size)]

            # Generate message
            msg = ECHOMessage(ECHOMessage.MSG_TYPE_INVOKE,
                              self.qid, "localhost", query)

            # Record timestamp
            time_of_queries[self.qid] = time.time()

            # Send a message
            sender.send(msg.serialize())
            self.qid += 1

            # Poisson process wait time
            nextTime = -log(1.0 - random.random()) / rate

            try:
                time.sleep((t0 + nextTime) - time.time())
            except IOError:
                # In case we have negative value in sleep parameter
                pass

        self.finishing()

    def finishing(self):

        # Recording current qid to a file
        confparser.set('Interface', 'start_qid', str(self.qid))
        with open(str(path[0]) + '/../config.cfg', 'w') as fp:
            confparser.write(fp)

        print "total sent : " + str(self.qid - START_QID)
        print 'Waiting 10 sec for unanswer queries to return'
        time.sleep(10)
        print 'Done'


def main():
    # Read command arguments
    try:
        args = get_args()
    except IOError as(errno, strerror):
        print "IOError({0}): {1}".format(errno, strerror)

    # Setup profiler
    Profiler.enabled = args.profile

    ##########################
    # perform load generator #
    ##########################
    print "Initializing..."
    daemon = LoadGenerator(args, '/tmp/load-gen.pid',
                           stdout=sys.stdout, stderr="load-gen.log")

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

    #Name of the process that is running (irrelevant of where it was started)
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
    try:
        exit(main())
    except KeyboardInterrupt:
        pass
    finally:
        pass
