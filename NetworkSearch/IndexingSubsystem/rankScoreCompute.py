""" Calculate rank score indexes.

It contains a RankScoreComputer class for providing
the functions to calculate the scores in advance.
With these scores, they help better performance of
the query subsystem.

@author: Misbah Uddin

 """

import collections
import pymongo


class RankScoreComputer():
    """ This class contains methods for rank score calculation for keyword and
    document based.

    The method format is following:

    one input argument : a original object to be computed a score
    yield: return an index object as a dict format one by one by 'yield'. The
           dict has to contain 'keyword' and 'document' keys

    *** Important: The active functions are defined by the FUNCTION_LIST.
        To disable a function, remove that function name from the list

    """
    def __init__(self):
        """ initiation of the class by assigning a list of ranking functions
        that will be called by indexManager"""

        self.FUNCTION_LIST = [
                              self.score_tf,
                              self.score_name_resolution,
                              self.score_type_resolution
                             ]

    def score_tf(self, obj):
        """ object -> generator(dict)

        return a generator object for returning an index object
        and a tf value."""

        #################
        # term indexing #
        #################
        if obj['content']:

            object_name = obj["object-name"]
            object_type = obj["object-type"]

            # TODO: have to confirm that the 'content' field depicts all
            # attributes and values in a object, and can contain a duplicate
            # value

            # Filter out not a base string and then count number of occurrences
            # TODO: assume that a base string is a slow changing value
            keywords = filter(
                          lambda x: isinstance(x, basestring), obj['content'])
            keywords_counter = collections.Counter(keywords)
            keywords_counts = keywords_counter.most_common()

            # Calculate tf-idf values
            # TODO: add calculation of idf
            max_tf = keywords_counts[0][1]
            for keyword, count in keywords_counts:
                yield {"keyword": keyword, "document": obj["_id"],
                       "object-type": object_type,
                       "object-name": object_name,
                       "tf": 0.5 + (0.5 * count) / float(max_tf)}

        else:
            # TODO: flatten dictionary
            print 'error cannot find ["content"]'

        ##################
        # phrase indexing #
        ##################
        # Get phrases
        phases = []
        for key, value in obj.iteritems():
            # TODO: do not include fast changing data,
            # need some way to define fast changing data, not a string?? maybe.

            # Ignore these field
            if key == "_id" or key == "content" or key == "last-updated":
                continue
            if isinstance(value, list):
                phases.extend([":".join([key, str(v)]) for v in value])
            else:
                phases.append(":".join([key, str(value)]))

        # Count number of occurrences
        phases_counter = collections.Counter(phases)
        phases_counts = phases_counter.most_common()

        # Calculate tf-idf values
        # TODO: add calculation of idf
        max_tf = phases_counts[0][1]
        for phase, count in phases_counts:
            yield {"keyword": phase, "document": obj["_id"],
                   "object-type": object_type,
                   "object-name": object_name,
                   "tf": 0.5 + (0.5 * count) / float(max_tf)}

        # TODO: merge term indexing and phase indexing coding if possible

    def score_name_resolution(self, obj):
        """ object -> generator(dict)

        return a generator object for returning an index object
        calculated by a name resolution method."""

        object_name = obj["object-name"]
        for partial_name in object_name.split(':'):
            if partial_name != 'ns':
                yield {"keyword": partial_name, "document": obj["_id"],
                       "object-type": obj["object-type"],
                       "object-name": object_name,
                       "nr": 1}

        # TODO consider "abb:sss" that match the name in object-name too

    def score_type_resolution(self, obj):
        """ object -> generator(dict)

        return a generator object for returning an index object
        calculated by a type resolution method."""

        yield {"keyword": obj['object-type'], "document": obj["_id"],
               "object-type": obj["object-type"],
               "object-name": obj["object-name"],
               "tr": 1}
