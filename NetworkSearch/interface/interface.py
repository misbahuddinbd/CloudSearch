""" A system interface

This module is a middleware between the system and a client,
served as an interface. There are two socket types connecting
to underlying systems and one socket types connecting to the
client.

@author: Misbah Uddin

"""

import logging
import threading
from multiprocessing import Process
import zmq

from NetworkSearch2.QuerySubsystem.echoMessage import ECHOMessage

#############################
# read a configuration file #
#############################
from ConfigParser import SafeConfigParser
from sys import path

confparser = SafeConfigParser()
confparser.read([str(path[0]) + '/config.cfg'])

# get values
INTERFACE_PORT = confparser.getint('Interface', 'interface_port')
DISPATCHER_PORT = confparser.getint('Dispatcher', 'dispatcher_port')
START_QID = confparser.getint('Interface', 'start_qid')

del confparser

EXTERNAL_PORT = 7735
#############################


class queryInterface(Process):
    """ A (sub)process for providing an interface (middleware) between
    the underlying systems and a client. The client will connect to the
    interface via the external port. """

    def __init__(self):
        super(queryInterface, self).__init__()

    def run(self):
        self.context = zmq.Context()
        # Open socket for receiving the result from underlying system.
        self.receiver = self.context.socket(zmq.PULL)
        self.receiver.bind("tcp://*:{}".format(INTERFACE_PORT))
        # Open socket for sending the query to the underlying system.
        self.sender = self.context.socket(zmq.PUSH)
        self.sender.connect("tcp://localhost:{}".format(DISPATCHER_PORT))

        t = threading.Thread(target=self.front_end_thread)
        t.start()

        logging.info("Interface initiated Successfully.")

        t.join()

    def front_end_thread(self):
        """ A thread for receive a query and execute a query in sequential."""
        # Query receiving socket
        self.server_socket = self.context.socket(zmq.REP)
        self.server_socket.bind("tcp://*:%s" % EXTERNAL_PORT)

        # Initiate the query's invoke_id
        i = START_QID

        while 1:
            # Receive a user query (QueryObject instance)
            query = self.server_socket.recv_pyobj()
            logging.debug("receive query : {}".format(query))

            # Create a message
            msg = ECHOMessage(ECHOMessage.MSG_TYPE_INVOKE,
                              i, "localhost", query)

            # Send a query for an execution, then receive
            self.sender.send(msg.serialize())
            digested_message = self.receiver.recv()
            msg = ECHOMessage.deserialize(digested_message)

            # Return only compacted results to client
            self.server_socket.send(msg.data)

            # Increase invoke_id
            i += 1
