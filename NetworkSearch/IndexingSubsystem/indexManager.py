""" Indexing module

It contains a daemon class to start the indexing subsystem.

@author: Misbah Uddin

"""

import sys
import logging
import argparse
import collections
import cPickle as pickle

import pymongo
import zmq

from NetworkSearch2.util.daemon import Daemon
from rankScoreCompute import RankScoreComputer

INDEXING_PORT = 7733


def get_args():
    """ None -> dict

    Argument parsing"""

    parser = argparse.ArgumentParser(
                         description="calculate rank score index module"
                         )
    parser.add_argument('-host', type=str, default="localhost",
                        help='A database host IPaddress')
    parser.add_argument('-port', type=int, default=27017,
                        help='A database host port')
    parser.add_argument('-indexdb', type=str, default="index",
                        help='A index database name')
    parser.add_argument('-indexcoll',  type=str, default="termdoc",
                        help='A index database collection')
    parser.add_argument("-debug", action='store_true', default=False,
                        help='add debug information to a log')
    parser.add_argument("mode", choices=['start', 'stop', 'restart'],
                        help='to start/stop/restart the Network Search module')
    return parser.parse_args()


class IndexManager(Daemon):

    """ Index Manager is a gateway to receiving an update from
    sensing subsystem and perform indexing.

    Note that : The received message is serialized by cPickle and has format
    (<operation>,<dict>) where <operation> is integer (1 : update, 2: delete),
    and <dict> is a python dictionary.

    """

    def __init__(self, args, pidfile, stdin='/dev/null',
                 stdout='/dev/null', stderr='/dev/null'):
        super(IndexManager, self).__init__(pidfile, stdin, stdout, stderr)
        self.args = args

    def initiation(self):

        args = self.args

        # Establish server socket
        context = zmq.Context()
        self.receiver = context.socket(zmq.PULL)
        self.receiver.bind("tcp://*:" + str(INDEXING_PORT))

        # Establish a connection to a database
        connection = pymongo.MongoClient(args.host, args.port)

        # Recreate index database
        connection[args.indexdb].drop_collection(args.indexcoll)
        self.collection = connection[args.indexdb][args.indexcoll]

        # Setup a mongodb index
        self.collection.ensure_index(
                          [("keyword", pymongo.ASCENDING),
                          ("document", pymongo.ASCENDING)], unique=True
                          )
        self.collection.ensure_index([("document", pymongo.ASCENDING)])

        # Create a rank score generator
        self.score_generator = RankScoreComputer()
        logging.info("Initiated")
        logging.info("End of initiation phase")

    def run(self):
        """ This method is called when IndexManager is started.
        It collects message and performs indexing. """

        logging.info("=" * 20)
        logging.info("Sensor subsystem module stated ")
        logging.info("=" * 20)

        # Initiation
        self.initiation()

        # Assign function addresses locally
        receiver = self.receiver

        while 1:
            # Receive a digested message from other nodes
            serialized_message = receiver.recv()
            operation, obj = pickle.loads(serialized_message)

            # Perform an operation
            if operation == 1:
                self.update(obj)
            elif operation == 2:
                self.delete(obj)
            else:
                self.invalid_case(obj)

    def update(self, obj):
        """ Calculate index objects and update/add them into the database.
        Note that: we need oid of the object"""

        # Get indexes associated to the object from database
        templist = list(self.collection.find(
                                    {"document": obj['_id']}, {"_id": 0})
                                    )
        updateIndexes = []

        # Grouped is for grouping up the index objects with the same keyword
        grouped = collections.defaultdict(dict)

        for func in self.score_generator.FUNCTION_LIST:
            for index_object in func(obj):
                grouped[index_object['keyword']].update(index_object)

        # Remove index from the temp list if it is the same as new one
        for item in grouped.values():
            try:
                templist.pop(templist.index(item))
            except ValueError:
                # New indexes
                updateIndexes.append(item)

        # Delete indexes
        deleteIndexes = templist

        # Delete indexes
        for index_object in deleteIndexes:
            self.collection.remove(index_object)

        # update indexes
        for index_object in updateIndexes:

            self.collection.update(
                                {"keyword": index_object.pop('keyword'),
                                "document": index_object.pop('document')},
                                {"$set": index_object}, upsert=True)

    def delete(self, obj):
        """ delete all index objects of this object based on its object id."""
        self.collection.remove({"document": obj['_id']})

    def invalid_case(self, obj):
        logging.warning("Received an unknown operation from the message")


def main():
    # Read command arguments
    try:
        args = get_args()
    except IOError as(errno, strerror):
        print "IOError({0}): {1}".format(errno, strerror)

    # setup a logging
    logging_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
                filename=str(sys.path[0]) + '/IndexManager.log',
                level=logging_level,
                format='%(asctime)s %(levelname)s: %(module)s: %(message)s',
                datefmt='%m/%d/%Y %I:%M:%S %p'
                )

    # setup a daemon
    daemon = IndexManager(args, '/tmp/indexManager.pid',
                          stdout=sys.stdout, stderr='IndexManager.log')

    if 'start' == args.mode:
        print 'started'
        daemon.start()
    elif 'stop' == args.mode:
        daemon.stop()
        print 'stopped'
    elif 'restart' == args.mode:
        daemon.restart()
    else:
        pass

if __name__ == "__main__":
    exit(main())
