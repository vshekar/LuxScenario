import sumolib
import networkx

class Graph():
    graph = {}
    edge_names = {}
    node_names = {}

    def add_edge(self, source, dest, name):
        if source in self.graph.keys():
            self.graph[source].append(dest)
        else:
            self.graph[source] = [dest]

        self.edge_names[(source, dest)] = name
        self.node_names[name] = (source, dest)

    def get_subnetwork(self, name, depth):
        source, dest = self.node_names[name]
        visited = set()
        #visited.add(source)

        visited |= self.bfs_search(source, depth, visited)
        visited |= self.bfs_search(dest, depth, visited)

        edge_names = set()
        self.subnetwork = Graph()

        for source in visited:
            if source in self.graph:
                for dest in self.graph[source]:
                    e_name = self.edge_names[(source, dest)]
                    edge_names.add(e_name)
                    if (dest, source) in self.edge_names:
                        e_name = self.edge_names[(dest, source)]
                        edge_names.add(e_name)
                #self.subnetwork.add_edge(source, dest, e_name)

        #edge_names.remove(name)
        return edge_names
    
    def size(self):
        return len(self.edge_names)

    def get_path_edges(self, start_edge, end_edge):
        a, start = self.node_names[start_edge]
        b, end = self.node_names[end_edge]
        path = [a] + self.find_path(start, end)
        edges = []
        for i,node in enumerate(path[:-1]):
            edges.append(self.edge_names[(node, path[i+1])])
        return edges

    def find_path(self, start, end, path=[]):
        path += [start]
        if start == end:
            return path
        if start not in self.graph.keys():
            return None
        shortest = None
        for node in self.graph[start]:
            if node not in path:
                newpath = self.find_path(node, end, path)
                if newpath:
                    if not shortest or len(newpath) < len(shortest):
                        shortest = newpath
        return shortest


    def bfs_search(self, start_node, depth, visited=set()):
        depth -= 1
        visited.add(start_node)
        if start_node in self.graph:
            for child in self.graph[start_node]:
                if depth > 0 and child not in visited:
                    self.bfs_search(child, depth, visited)

        return visited

def get_lambdas(net_file):
    net = sumolib.net.readNet(net_file)
    lambdas = {}
    
    network_rep = Graph()
    #network_rep = networkx.DiGraph()
    vulnerable_edges = [e for e in net.getEdges() if e.getLaneNumber()>2]


    for edge in net.getEdges():
        network_rep.add_edge(edge.getFromNode().getID(), edge.getToNode().getID(), edge.getID())
    #    network_rep.add_edge(edge.getFromNode().getID(), edge.getToNode().getID(), id=edge.getID())
    

    total_edges = network_rep.size()
    print("Total Edges: {}".format(total_edges))

    for disrupted in vulnerable_edges:
        total_edges = network_rep.size() 
        lmbd = 250
        subnetwork_edges = network_rep.get_subnetwork(disrupted.getID(), lmbd)
        dis_from = disrupted.getFromNode().getID()
        dis_to = disrupted.getToNode().getID()

        #subnetwork_edges = list(networkx.bfs_edges(network_rep, source=dis_from, depth_limit=lmbd))
        while(len(subnetwork_edges) != total_edges):
            #print("{} < {} : {}".format(len(subnetwork_edges), total_edges, lmbd))
            lmbd += 1
            #subnetwork_edges = list(networkx.bfs_edges(network_rep, source=dis_from, depth_limit=lmbd))
            total_edges = len(subnetwork_edges)
            subnetwork_edges = network_rep.get_subnetwork(disrupted.getID(), lmbd)   
            
        while(len(subnetwork_edges) == total_edges and lmbd > 0):
            lmbd -= 1
            #subnetwork_edges = list(networkx.bfs_edges(network_rep, source=dis_from, depth_limit=lmbd))
            total_edges = len(subnetwork_edges)
            subnetwork_edges = network_rep.get_subnetwork(disrupted.getID(), lmbd)
        
        dis_id = disrupted.getID()
        lambdas[dis_id] = lmbd
        print("{} : {}".format(dis_id, lmbd))
    return lambdas
        
if __name__=="__main__":
    l = get_lambdas('../scenario/lust.net.xml')
    print(l)