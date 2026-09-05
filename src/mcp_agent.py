# src/mcp_agent.py
import json
import networkx as nx
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

class MCPAgent:
    def __init__(self):
        self.graph = nx.DiGraph()

    def ingest_usecases(self, usecases_file):
        """Ingesta un archivo de casos de uso específico"""
        data = json.load(open(usecases_file, encoding="utf-8"))
        lib_name = data[0]["title"].split("-")[-1].strip() if data else "Libreria"

        # Evitar duplicados de librería
        if not self.graph.has_node(lib_name):
            self.graph.add_node(lib_name, type="library")

        for uc in data:
            case = uc["title"].strip()
            script = uc["script"].strip()

            # Evitar duplicados de casos
            if not self.graph.has_node(case):
                self.graph.add_node(case, type="usecase")

            # Evitar duplicados de scripts
            if not self.graph.has_node(script):
                self.graph.add_node(script, type="script")

            # Evitar duplicados de aristas
            if not self.graph.has_edge(lib_name, case):
                self.graph.add_edge(lib_name, case, relation="tiene")
            if not self.graph.has_edge(case, script):
                self.graph.add_edge(case, script, relation="ejemplificado_por")

        return lib_name

    def ingest_all_usecases(self):
        """Ingesta todos los archivos usecases_*.json en la carpeta data/"""
        files = list(DATA_DIR.glob("usecases_*.json"))
        for f in files:
            data = json.load(open(f, encoding="utf-8"))
            if not data or not isinstance(data, list):
                continue
            lib_name = data[0]["title"].split("-")[-1].strip()

            if not self.graph.has_node(lib_name):
                self.graph.add_node(lib_name, type="library")

            for uc in data:
                case = uc["title"].strip()
                script = uc["script"].strip()

                if not self.graph.has_node(case):
                    self.graph.add_node(case, type="usecase")
                if not self.graph.has_node(script):
                    self.graph.add_node(script, type="script")

                if not self.graph.has_edge(lib_name, case):
                    self.graph.add_edge(lib_name, case, relation="tiene")
                if not self.graph.has_edge(case, script):
                    self.graph.add_edge(case, script, relation="ejemplificado_por")

        print(f"Ingestados {len(files)} archivos en el grafo.")

    def list_libraries(self):
        return [n for n, d in self.graph.nodes(data=True) if d.get("type") == "library"]

    def query_usecases(self, library):
        if library not in self.graph:
            return []
        return [n for n in self.graph.successors(library) if self.graph[library][n]["relation"] == "tiene"]

    def query_scripts(self, case):
        if case not in self.graph:
            return []
        return [n for n in self.graph.successors(case) if self.graph[case][n]["relation"] == "ejemplificado_por"]

    def export_graph(self, path="data/knowledge_graph.gexf"):
        nx.write_gexf(self.graph, path)
        print(f"Grafo exportado a {path}")

if __name__ == "__main__":
    agent = MCPAgent()
    agent.ingest_all_usecases()
    print("Librerías disponibles:", agent.list_libraries())
    for lib in agent.list_libraries():
        print(f"Casos de uso de {lib}:", agent.query_usecases(lib))
    agent.export_graph("data/knowledge_graph.gexf")
