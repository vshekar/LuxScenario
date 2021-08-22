import numpy as np
from collections import defaultdict, deque

class Data:
    def __init__(self, lmbd, start_time, end_time, edge):
        self.lmbd = lmbd
        self.start_time = start_time
        self.end_time = end_time
        self.edge = edge
        self._dataframe = None

    #def gen_name(self):
        #return "{}_{}_{}_{}".format(self.edge, self.dis_start, self.dis_end, self.lmbd)

    #@property
    def get_dataframe(self):
        return self._dataframe

    #@dataframe.setter
    def set_dataframe(self, val):
        self._dataframe = np.array(val, dtype=[('vehicle', 'S50'), ('start_time', 'i'), ('end_time', 'i')])

class Graph:
    def __init__(self):
        self.graph = defaultdict(set)
        self.names = defaultdict(list)
        self.nodes = {}

    def addEdge(self, u, v, name):
        self.graph[u].add(v)
        self.graph[v].add(u)
        self.names[(u, v)].append(name)
        self.nodes[name] = (u,v)

    def getSubnet(self, edge, depth):
        s = edge.getFromNode().getID()
        d = edge.getToNode().getID()
        #print(s, d)
        visited_edges = self.BFS(s, depth)
        visited_edges2 = self.BFS(d, depth)
        #print(visited_edges, visited_edges2)
        visited_edges = visited_edges.union(visited_edges2)
        return visited_edges

    def BFS(self, s, depth):
        visited = defaultdict(bool)
        visited_edges = set()
        queue = deque([])
        queue.append(s)
        visited[s] = True

        for d in range(depth, 0, -1):
            next_queue = deque([])
            while(queue):
                s = queue.pop()

                #print(self.graph[s])
                for child in self.graph[s]:
                    if not visited[child]:
                        next_queue.append(child)
                        visited[child] = True
                    
                    if (s, child) in self.names:
                        for name in self.names[(s,child)]:
                            visited_edges.add(name)
                       
                    if (child, s) in self.names:
                        for name in self.names[(child, s)]:
                            visited_edges.add(name)
            queue = next_queue
        return visited_edges
