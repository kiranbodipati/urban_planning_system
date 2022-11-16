import nxneo4j as nxneo4j
import json
from neo4j import GraphDatabase

def read_json(file_path):
    f = open(file_path)
    data = json.load(f)
    f.close()
    
    return data

def load(fname):
    G = nxneo4j.DiGraph(driver)
    d = read_json(fname)
    nodes_list = []
    bus_bus_links = []
    node_attr = {}
    for nodes in d['nodes'][:50]:
        G.add_node(nodes['id'])                 
        node_attr[nodes['id']] = {'latitude':float(nodes['latitude']),'longitude':float(nodes['longitude'])}
    nxneo4j.set_node_attributes(G, node_attr)
    for links in d['links'][:50]:
        G.add_edge(links['source'],links['target'],type = links['type'],weight=links['weight'])
    return G

def load_graph_nodes(fname):
    d = read_json(fname)
    nodes_info = {}
    for nodes in d['nodes']:
        nodes_info[nodes['id']]=nodes
    return nodes_info

class App:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        # Don't forget to close the driver connection when you are finished with it
        self.driver.close()
        
    def create_nodes(self,node_type,source_node):
         with self.driver.session(database="neo4j") as session:
            # Write transactions allow the driver to handle retries and transient errors
            result = session.execute_write(
                self._create_bus_nodes,node_type,source_node)

    def create_relationships(self,link_type,source_node,target_node,weight):
        with self.driver.session(database="neo4j") as session:
            # Write transactions allow the driver to handle retries and transient errors
            result = session.execute_write(
                self._create_and_return_friendship,link_type,source_node,target_node,weight)

    @staticmethod
    def _create_bus_nodes(tx,node_type,node):
        query = (
        """
        CREATE (n:bus_node {busstop_id:$source_id,latitude:$lat1,longitude:$long1})
        """)
        result = tx.run(query,node_type=node_type,
                        lat1=node['latitude'],
                        long1=node['longitude'],
                        source_id = str(node['id']))
        
    @staticmethod
    def _create_and_return_friendship(tx, link_type, source_node, target_node, weight):
        # To learn more about the Cypher syntax, see https://neo4j.com/docs/cypher-manual/current/
        # The Reference Card is also a good resource for keywords https://neo4j.com/docs/cypher-refcard/current/
        query = (
        """
        MATCH (n1),(n2)
        WHERE n1.busstop_id = $busstop1 AND n2.busstop_id = $busstop2
        CREATE (n1)-[:bus_bus {weight: $weight,name:$link_type}]->(n2)
        return n1,n2
        """)
        
        result = tx.run(query,link_type=link_type,
                        busstop1=source_node['id'],busstop2=target_node['id'],
                        weight=weight)
        
    def find_person(self, bus_stop):
        with self.driver.session(database="neo4j") as session:
            result = session.execute_read(self._find_and_return_person, bus_stop)
            for row in result:
                return False
        return True
    
    def _find_and_return_person(tx, bus_stop):
        query = (
            "MATCH (n) "
            "WHERE n.busstop_id = $bus_stop "
            "RETURN n"
        )
        result = tx.run(query, bus_stop=bus_stop)
        return [row for row in result]


if __name__ == "__main__":
    # define credentials
    uri      = "neo4j+s://2c5e8457.databases.neo4j.io:7687" 
    user     = "neo4j"
    password = 'C3DKuamyGb64q9f8ldtq4u0N9Jjxag-9eRPceC0MwPQ'

    delete_bool = False # set to true if you want to delete all nodes and input data again

    # set up connection to graph database
    driver = GraphDatabase.driver(uri=uri,auth=(user,password))

    if(delete_bool):
        transport_graph = nxneo4j.DiGraph(driver) 
        transport_graph.delete_all() 
    fname = '/kaggle/input/bus-train-info/bus_transport_graph.json'
    app = App(uri, user, password)
    nodes_info = load_graph_nodes(fname)
    d = read_json(fname)
    nodes_list = []
    nodes_list = list(set(nodes_list))
    for n in nodes_info:
        app.create_nodes('busstop',nodes_info[n])
    print('uploaded nodes')
    for links in d['links']:
        source_node = nodes_info[links['source']]
        target_node = nodes_info[links['target']]
        weight = links['weight']
        app.create_relationships('bus_bus',source_node,target_node,weight)
    print('uploaded relationships')
    app.close()