from collections import defaultdict, deque
import sumolib
import json

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


def get_lambdas(net_file):
    net = sumolib.net.readNet(net_file)
    net_graph = Graph()
    lambdas = {}
    v_e = {}

    vulnerable_edges = [e for e in net.getEdges() if e.getLaneNumber()>2]
    #vulnerable_edges = [e for e in net.getEdges() if e.getID()=='-31230#1']

    for edge in net.getEdges():
        net_graph.addEdge(edge.getFromNode().getID(), edge.getToNode().getID(), edge.getID())
    
    #print(len(net_graph.graph))

    for e in vulnerable_edges:
        #n = e.getFromNode().getID()       
        #visited, visited_edges = net_graph.BFS(n, 1)
        old_visited_edges = net_graph.getSubnet(e, 20)
        visited_edges = net_graph.getSubnet(e, 21)
        lmbd = 21
        while len(old_visited_edges) != len(visited_edges):
            old_visited_edges = visited_edges
            lmbd += 1
            visited_edges = net_graph.getSubnet(e, lmbd)
        lambdas[e.getID()] = lmbd
        print("{} : {}".format(e.getID(), lmbd))
        #v_e[e.getID()] = visited_edges

    #print(lambdas)
    return lambdas
    """
    print(len(v_e['-31230#1']))
    with open('selection.txt', 'w') as f:
        s = ""
        for e in v_e['-31230#1']:
            s += "edge:{}\n".format(e)
        f.write(s)
    """

if __name__=="__main__":
    l = get_lambdas('../scenario/lust.net.xml')
    with open('lambdas.json','w') as f:
        json.dump(l, f)
    