import math
import random
import pygame

PHEROMONES: list[str] = ["grocery store", "nest"]

def initiate_pheromone_dict(value:float = 0) -> dict[str,float]:
    pheromones:dict[str,float] = {}
    for pheromone in PHEROMONES:
        pheromones[pheromone] = value
    return pheromones

FRAMERATE = 60
WIDTH,HEIGHT = 1280,720
MARGIN = 10
NODECOLOURS:dict[str|None,pygame.typing.ColorLike] = {
    None: (0,0,0),
    "grocery store": (0,0,255),
    "nest": (255,0,0)
}
NODERADIUS = 5
PATHCOLOUR = (0,0,0)
PATHWIDTH = 1
ANTCOLOUR = (0,255,0)
ANTSIZE = 8

ANTSPEED = 100/FRAMERATE
WANDERCHANCE = 0.01/FRAMERATE
DROPRATE = 0.01/FRAMERATE
NEEDDECAY = 0.001/FRAMERATE
FACILITYUSERATE = 0.1/FRAMERATE
FULFILLMENT = 1

nodes: dict[int, Node] = {}
paths: list[Path] = []
ants: list[Ant] = []

class Path:
    origin: int
    destination: int
    pheromones: dict[str,float]
    
    def __init__(self, origin: int, destination: int, pheromones:dict[str,float]|None = None):
        self.origin = origin
        self.destination = destination
        self.pheromones = pheromones if pheromones is not None else initiate_pheromone_dict()
        
    def __repr__(self):
        return f"Path(origin={self.origin},destination={self.destination},pheromones={self.pheromones})"
    
    def __str__(self):
        return f"Path(origin={nodes[self.origin]},destination={nodes[self.destination]},pheromones={self.pheromones})"
        
    def draw(self, surface: pygame.Surface) -> None:
        start = nodes[self.origin]
        end = nodes[self.destination]
        pygame.draw.line(surface, color=PATHCOLOUR, start_pos=(round(start.x),round(start.y)), end_pos=(round(end.x),round(end.y)), width=PATHWIDTH)

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
    
    def __init__(self, id: int, x: float, y: float, facility: str|None, connections: list[int]):
        self.id = id
        self.x = x
        self.y = y
        self.facility = facility
        self.connections = connections
        
    def __repr__(self):
        return f"Node(id={self.id},x={self.x},y={self.y},facility={self.facility},connections={self.connections})"
    
    def draw(self, surface: pygame.Surface):
        pygame.draw.circle(surface=surface, color=NODECOLOURS[self.facility],center=(self.x,self.y),radius=NODERADIUS)
    
    def get_paths(self) -> list[Path]:
        path_objects: list[Path] = []
        for connection in self.connections:
            path = get_path(self.id, connection)
            if path is None:
                print(f"WARNING: no path between {self} and {nodes[connection]}. Creating new entry.")
                path = Path(origin=self.id, destination=connection, pheromones=initiate_pheromone_dict())
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
    goal: str|None
    
    def __init__(self, origin: int, destination:int|None = None, distance:float = 0, nest:int|None = None, needs:dict[str,float]|None = None, pheromones:dict[str,float]|None = None, goal:str|None = None):
        self.origin = origin
        self.destination = destination if destination is not None else origin
        self.distance = distance
        self.nest = nest if nest is not None else origin
        self.needs = needs if needs is not None else initiate_pheromone_dict()
        self.pheromones = pheromones if pheromones is not None else initiate_pheromone_dict()
        self.goal = goal
    
    def get_pos(self) -> tuple[float,float]:
        if self.origin != self.destination:
            origin = nodes[self.origin]
            destination = nodes[self.destination]
            path = get_path(self.origin,self.destination)
            assert path is not None
            fraction_traveled = self.distance/path.get_length()
            x = origin.x+fraction_traveled*(destination.x-origin.x)
            y = origin.y+fraction_traveled*(destination.y-origin.y)
        else:
            origin = nodes[self.origin]
            x,y = origin.x, origin.y
        return (x,y)
    
    def draw(self, surface: pygame.Surface):
        x,y = self.get_pos()
        pygame.draw.rect(surface,color=ANTCOLOUR,rect=pygame.Rect((x-ANTSIZE/2),(y-ANTSIZE/2),ANTSIZE,ANTSIZE))

    def step(self, speed:float = ANTSPEED) -> None:
        if self.goal is not None and nodes[self.origin].facility == self.goal and self.needs[self.goal] <= FULFILLMENT:
            self.utilise_facility(self.origin)
        else:
            self.distance += speed
            path = get_path(self.origin, self.destination)
            assert path is not None
            while self.distance >= path.get_length():
                if self.goal is not None and nodes[self.destination].facility == self.goal and self.needs[self.goal] <= FULFILLMENT:
                    self.utilise_facility(self.destination)
                    break
                else:
                    self.distance -= path.get_length()
                    self.origin = self.destination
                    self.choose_destination()
                    path = get_path(self.origin, self.destination)
                    assert path is not None

    def choose_destination(self, wander_chance:float = WANDERCHANCE):
        if self.goal is not None and self.needs[self.goal] <= FULFILLMENT:
            need = self.goal
        else:
            need = self.get_highest_need()
            self.goal = self.get_highest_need()
        assert need is not None
        connected_paths = [get_path(self.origin, connection) for connection in nodes[self.origin].connections]
        assert all([path is not None for path in connected_paths])
        path_weights: list[float] = []
        for path in connected_paths:
            if path is not None:
                pheromone_amount = path.pheromones[need]
                if pheromone_amount != 0:
                    path_weights.append(pheromone_amount)
                else:
                    path_weights.append(wander_chance)
            else:
                path_weights.append(0)
        chosen_path: Path|None = random.choices(connected_paths, weights=path_weights)[0]
        assert chosen_path is not None
        self.drop_pheromones(chosen_path)
        if chosen_path.origin == self.origin:
            self.destination = chosen_path.destination
        else:
            self.destination = chosen_path.origin

    def get_highest_need(self) -> str|None:
        highest_need: str|None = None
        highest_value: float = -1
        for need in self.needs.keys():
            if self.needs[need] > highest_value:
                highest_need = need
        return highest_need

    def utilise_facility(self, node: int) -> None:
        facility = nodes[node].facility
        assert facility is not None
        self.needs[facility] += FACILITYUSERATE
        self.pheromones[facility] += FACILITYUSERATE

    def drop_pheromones(self, path: Path, drop_rate:float = DROPRATE) -> None:
        for pheromone in self.pheromones.keys():
            drop_amount = self.pheromones[pheromone]*drop_rate
            self.pheromones[pheromone] -= drop_amount
            path.increase_pheromones(pheromone, drop_amount)
          
if __name__ == "__main__":
    node_amount = random.randint(5,10)
    path_amount = random.randint(node_amount,(node_amount*(node_amount-1))//4)
    ant_amount = 1#random.randint(1,node_amount//2)
    for i in range(node_amount):
        if i < len(PHEROMONES):
            facility = PHEROMONES[i]
        else:
            facility = random.choices(population=[*PHEROMONES,None],
                                      weights=[1 if i != len(PHEROMONES) else 20
                                               for i in range(len(PHEROMONES)+1)])[0]
        nodes[i] = Node(id=i,
                        x=random.random()*(WIDTH-2*MARGIN)+MARGIN,
                        y=random.random()*(HEIGHT-2*MARGIN)+MARGIN,
                        facility=facility,
                        connections=[])
    print("Initiated nodes")
    for i in range(path_amount):
        node1 = random.randint(0, node_amount-1)
        while len(nodes[node1].connections) >= (path_amount/node_amount)*3:
            print(nodes[node1])
            node1 = random.randint(0, node_amount-1)
        node2 = random.randint(0, node_amount-1)
        while node1 == node2 or node2 in nodes[node1].connections:
            node2 = random.randint(0, node_amount-1)
        nodes[node1].connections.append(node2)
        nodes[node2].connections.append(node1)
        paths.append(Path(origin=node1,destination=node2))
    for node in nodes.values():
        if len(node.connections) == 0:
            node2 = random.randint(0, node_amount-1)
            while node.id == node2:
                node2 = random.randint(0, node_amount-1)
            node.connections.append(node2)
            nodes[node2].connections.append(node.id)
            paths.append(Path(origin=node.id,destination=node2))
    print("Initiated paths")
    for i in range(ant_amount):
        nests:list[int] = []
        for node in nodes.values():
            if node.facility == "nest":
                nests.append(node.id)
        ants.append(Ant(origin=random.choice(nests)))
        ants[i].choose_destination()
    print("Initiated ants")
    
    pygame.init()
    screen = pygame.display.set_mode((WIDTH,HEIGHT))
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        screen.fill((255,255,255))
        
        for node in nodes.values():
            node.draw(screen)
        for path in paths:
            path.draw(screen)
        for ant in ants:
            ant.step()
            ant.draw(screen)
        if ants[0].goal is not None: print(ants[0].goal, ants[0].needs[ants[0].goal])
        
        pygame.display.flip()
        clock.tick(FRAMERATE)
        # print(clock.get_fps())
        
    pygame.quit()