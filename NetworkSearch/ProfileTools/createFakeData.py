""" generate fake data by double up the current data"""

import pymongo
import random
import time
from datetime import datetime
import zmq

from NetworkSearch.queryInterface import queryInterface

WAITING_INTERVAL = 1
number_of_object_wanted_per_server = 5000

server_names = ["cloud-1", "cloud-2", "cloud-3", "cloud-4", "cloud-5",
                "cloud-6", "cloud-7", "cloud-8", "cloud-9"]
#server_names = ['localhost']


def _flatten_to_list(x):
    """ flatten nested dicts, lists, tuples, or sets generators to lists"""

    # if x is a dict, we need to pop both values and keys
    if isinstance(x, dict):
        for key in x.iterkeys():
            yield key
        for value in x.itervalues():
            for item in _flatten_to_list(value):
                yield item
    # if x is a list, tuple, or set pop out each item
    elif isinstance(x, (list, tuple, set)):
        for item in x:
            for subitem in _flatten_to_list(item):
                yield subitem
    else:
        yield x


if __name__ == "__main__":

    for server_name in server_names:
        print server_name + " start"
        objsColl = pymongo.MongoClient(server_name, 27017)["sensor"]["objects"]
        # a connection to index system
        index_connector = zmq.Context().socket(zmq.PUSH)
        index_connector.connect("tcp://" + server_name + ":7733")

        num_round = 0
        while 1:
            num_round += 1
            # sleep between run
            time.sleep(WAITING_INTERVAL)
            sysSize = objsColl.count()
            print 'start {0} round, {1} size = {2}'.format(num_round,
                                                           server_name,
                                                           sysSize)
            # if it is reach the wanted size then stop
            if sysSize >= number_of_object_wanted_per_server:
                print server_name + ' DONE'
                break

            for obj in objsColl.find({'fake': {'$exists': False}},
                                     {'_id': 0, 'content': 0})[:]:
                # get a object type of the object
                objtype = str(obj['object-type'])

                # change name of server object
                if objtype == "server":
                    obj['object-name'] = obj['object-name'][:-1] + \
                          str(int(obj['object-name'][-1:]) + (10 * num_round))

                # change name of the server attribute
                if 'server' in obj:
                    obj['server'] = obj['server'][:-1] + \
                            str(int(obj['server'][-1:]) + (10 * num_round))

                # change hostname of the server attribute
                if 'hostname' in obj:
                    obj['hostname'] = obj['hostname'][:-1] + \
                            str(int(obj['hostname'][-1:]) + (10 * num_round))

                # change name of the vm attribute
                if 'vm' in obj:
                    if isinstance(obj['vm'], basestring):
                        obj['vm'] = obj['vm'] + '-' + str(num_round)
                    else:
                        for i in range(0, len(obj['vm'])):
                            obj['vm'][i] = obj['vm'][i] + '-' + str(num_round)

                # change name of the customers attribute
                if 'customer' in obj:
                    obj['customer'] = obj['customer'][:-1] +\
                                      '-' + str(num_round)

                # change id of the new customer
                if objtype == "customer":
                    obj['id'] = str(int(obj['id']) + 100 * num_round)

                # change name of others
                if not (objtype in ["customer", "server",
                                    "vm", "network-interface"]):
                    obj['object-name'] = obj['object-name'] +\
                            '_fake_' + str(random.randint(0, 999999))

                # add a fake attribute
                obj['fake'] = True
                obj["keyword"] = 100000000  # TODO: just added without testing
                obj["writeFake"] = 1

                # add content and date modified
                obj['content'] = list(_flatten_to_list(obj))
                obj['last-updated'] = datetime.now()
#                 print obj.values()

                # insert a fake object
                objsColl.insert(obj)

                # update the index database
                index_connector.send_pyobj([1, obj])
