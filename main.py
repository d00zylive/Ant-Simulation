import math

PHEROMONES: dict[str,float] = {
    "grocery store": 0,
    "house": 0,
}

nodes: dict[int, Node] = {}
paths: list[Path] = []
ants: list[Ant] = []

class Path:
    origin: int
    destination: int
    pheromones: dict[str,float]
    
    def __init__(self, origin: int, destination: int, pheromones: dict[str,float]):
        self.origin = origin
        self.destination = destination
        self.pheromones = pheromones

    def increase_pheromones(self, type: str, amount: float) -> None:
        if not type in self.pheromones.keys():
            print(f"WARNING: given type not recognised by {self}. Creating new entry.")
            self.pheromones[type] = 0
        self.pheromones[type] += amount
        
    def evaporate_pheromones(self, rate: float) -> None:
        for key in self.pheromones.keys():
            self.pheromones[key] *= rate
            
    def get_length(self) -> float:
        origin_node, destination_node = nodes[self.origin], nodes[self.destination]
        return math.sqrt((origin_node.x-destination_node.x)**2+(origin_node.y+destination_node.y)**2)

def get_path(node1: int, node2: int) -> Path|None:
    for path in paths:
        if path.origin == node1 and path.destination == node2 or path.destination == node1 and path.origin == node2:
            return path

class Node:
    id: int
    x: float
    y: float
    facility: str|None
    connections: list[int]
    
    def get_paths(self) -> list[Path]:
        path_objects: list[Path] = []
        for connection in self.connections:
            path = get_path(self.id, connection)
            if path is None:
                print(f"WARNING: no path between {self} and {nodes[connection]}. Creating new entry.")
                path = Path(origin=self.id, destination=connection, pheromones=PHEROMONES)
                paths.append(path)
            path_objects.append(path)
        return path_objects

class Ant:
    origin: int
    destination: int
    distance: float
    nest: int
    needs: dict[str,float]
    pheromones: dict[str,float]

    def step(self, speed: float) -> None:
        self.distance += speed
        path = get_path(self.origin, self.destination)
        assert path is not None
        while self.distance >= path.get_length():
            self.distance -= path.get_length()
            self.origin = self.destination
            self.destination = self.choose_path()
            path = get_path(self.origin, self.destination)
            assert path is not None

    def choose_path(self) -> int:
        pass

    def get_highest_need(self) -> str:
        pass

    def utilise_facility(self) -> None:
        pass

    def drop_pheromones(self) -> None:
        pass