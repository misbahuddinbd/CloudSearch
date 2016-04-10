import random
from collections import defaultdict
from math import log,exp

nodes = ["cloud-1","cloud-2","cloud-3","cloud-4","cloud-5","cloud-6","cloud-7","cloud-8","cloud-9"]
size = len(nodes)
N_longlink = 1
links = defaultdict(set)

def small_world():
    for node in nodes:
        #links[node] = random.sample(nodes-set([node]),2)
        
        self_index = nodes.index(node)
        # create ring
        links[node].add(nodes[(self_index+1)%size])
        links[nodes[(self_index+1)%size]].add(node)
        
        # create long links
        for _ in range(0,N_longlink):
            distance_from_node = exp(log(size)*(random.random() - 1.0))*size
            links[node].add(nodes[(self_index+int(distance_from_node))%size])
            links[nodes[(self_index+int(distance_from_node))%size]].add(node)
    #DONE
    #printing
    for link in sorted(links.iteritems()):
        print link[0] +" : " + ",".join(link[1])

if __name__=="__main__":
    small_world()
        