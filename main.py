import math
import random
import pygame

PHEROMONES: list[str] = ["store"]

def initiate_pheromone_dict(value:float = 0, nest:int|None = None) -> dict[str|int,float]:
    pheromones:dict[str|int,float] = {}
    for pheromone in PHEROMONES:
        pheromones[pheromone] = value
    if nest is None:
        for nest_node in nests:
            pheromones[nest_node] = value
    else:
        pheromones[nest] = value
    return pheromones

FRAMERATE = 10
WIDTH,HEIGHT = 1280,720
MARGIN = 10
NODECOLOURS:dict[str|None,pygame.typing.ColorLike] = {
    None: (0,0,0),
    "store": (0,255,0),
    "nest": (255,0,0)
}
FACILITYRADIUS = 7
NODERADIUS = 2
PATHCOLOURRAMP = 0.01
PATHWIDTH = 2
ANTCOLOUR = (0,0,255)
ANTSIZE = 8

SIMSPEED = 10
ANTSPEED = 100*SIMSPEED/FRAMERATE
WANDERCHANCE = 0.001
DROPRATE = 0.5
NEEDGROWTH = 0.05*SIMSPEED/FRAMERATE
FACILITYUSERATE = 0.5*SIMSPEED/FRAMERATE
PHEROMONERESET = 1
EVAPORATIONRATE = 0.97**(1*SIMSPEED/FRAMERATE)

nodes: dict[int, Node] = {}
paths: list[Path] = []
ants: list[Ant] = []
nests: list[int] = []

class Path:
    origin: int
    destination: int
    pheromones: dict[str|int,float]
    
    def __init__(self, origin: int, destination: int, pheromones:dict[str|int,float]|None = None):
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
        ramp = lambda x: min(x*100,255)#(255-(1/(PATHCOLOURRAMP*x+1/255))) if x != 0 else 0
        nest_pheromone_sum = round(ramp(sum(self.pheromones[pheromone] if isinstance(pheromone,int) else 0 for pheromone in self.pheromones.keys())))
        pygame.draw.line(surface, color=(nest_pheromone_sum,round(ramp(self.pheromones["store"])),0), start_pos=(round(start.x),round(start.y)), end_pos=(round(end.x),round(end.y)), width=PATHWIDTH)

    def increase_pheromones(self, type: str|int, amount: float) -> None:
        if not type in self.pheromones.keys():
            print(f"WARNING: given type not recognised by {self}. Creating new entry.")
            self.pheromones[type] = 0
        self.pheromones[type] += amount
        
    def evaporate_pheromones(self, rate:float = EVAPORATIONRATE) -> None:
        for key in self.pheromones.keys():
            self.pheromones[key] *= rate
            
    def get_length(self) -> float:
        origin_node, destination_node = nodes[self.origin], nodes[self.destination]
        return math.sqrt((origin_node.x-destination_node.x)**2+(origin_node.y-destination_node.y)**2)

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
        radius = NODERADIUS if self.facility is None else FACILITYRADIUS
        pygame.draw.circle(surface=surface, color=NODECOLOURS[self.facility],center=(self.x,self.y),radius=radius)
    
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
    needs: dict[str|int,float]
    pheromones: dict[str|int,float]
    goal: str|int|None
    
    def __init__(self, origin: int, destination:int|None = None, distance:float = 0, nest:int|None = None, needs:dict[str|int,float]|None = None, pheromones:dict[str|int,float]|None = None, goal:str|int|None = None):
        self.origin = origin
        self.destination = destination if destination is not None else origin
        self.distance = distance
        self.nest = nest if nest is not None else origin
        self.needs = needs if needs is not None else initiate_pheromone_dict(value=1, nest=self.nest)
        self.pheromones = pheromones if pheromones is not None else initiate_pheromone_dict(nest=self.nest)
        self.goal = goal
    
    def get_pos(self) -> tuple[float,float]:
        if self.origin != self.destination:
            origin = nodes[self.origin]
            destination = nodes[self.destination]
            path = get_path(self.origin,self.destination)
            assert path is not None
            fraction_traveled = self.distance/path.get_length()
            if fraction_traveled <= 1:
                x = origin.x+fraction_traveled*(destination.x-origin.x)
                y = origin.y+fraction_traveled*(destination.y-origin.y)
            else:
                x,y = destination.x,destination.y
        else:
            origin = nodes[self.origin]
            x,y = origin.x, origin.y
        return (x,y)
    
    def draw(self, surface: pygame.Surface):
        x,y = self.get_pos()
        pygame.draw.rect(surface,color=ANTCOLOUR,rect=pygame.Rect((x-ANTSIZE/2),(y-ANTSIZE/2),ANTSIZE,ANTSIZE))

    def step(self, speed:float = ANTSPEED) -> None:
        for need in self.needs.keys():
            self.needs[need] += NEEDGROWTH
                
        if self.goal is not None and (self.origin == self.goal or nodes[self.origin].facility == self.goal) and self.needs[self.goal] > 0:
            self.utilise_facility(self.origin)
            if self.needs[self.goal] <= 0:
                self.goal = self.get_highest_need()
        else:
            self.distance += speed
            path = get_path(self.origin, self.destination)
            if path is None:
                self.choose_destination()
                path = get_path(self.origin, self.destination)
                assert path is not None
            while self.distance >= path.get_length():
                if self.goal is not None and (self.destination == self.goal or nodes[self.destination].facility == self.goal) and self.needs[self.goal] > 0:
                    self.utilise_facility(self.destination)
                    self.distance = path.get_length()
                    break
                else:
                    self.distance -= path.get_length()
                    previous_node = self.origin
                    self.origin = self.destination
                    self.choose_destination(previous_node=previous_node)
                    path = get_path(self.origin, self.destination)
                    assert path is not None

    def choose_destination(self, previous_node:int|None = None, wander_chance:float = WANDERCHANCE):
        if self.goal is not None and self.needs[self.goal] > 0:
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
                if previous_node is not None and (previous_node == path.origin or previous_node == path.destination):
                    modifier = 0.1
                else:
                    modifier = 1
                pheromone_amount = path.pheromones[need]
                if pheromone_amount != 0:
                    path_weights.append(pheromone_amount*modifier)
                else:
                    path_weights.append(wander_chance*modifier)
            else:
                path_weights.append(0)
        chosen_path: Path|None = random.choices(connected_paths, weights=path_weights)[0]
        assert chosen_path is not None
        self.drop_pheromones(chosen_path)
        if chosen_path.origin == self.origin:
            self.destination = chosen_path.destination
        else:
            self.destination = chosen_path.origin

    def get_highest_need(self) -> str|int|None:
        highest_need: str|int|None = None
        highest_value: float = -math.inf
        for need in self.needs.keys():
            if self.needs[need] > highest_value:
                highest_need = need
                highest_value = self.needs[need]
        return highest_need

    def utilise_facility(self, node: int) -> None:
        facility = nodes[node].facility
        assert facility is not None
        if facility != "nest":
            self.needs[facility] -= FACILITYUSERATE
            self.pheromones[facility] = PHEROMONERESET
        else:
            assert node == self.nest
            self.needs[self.nest] -= FACILITYUSERATE
            self.pheromones[self.nest] = PHEROMONERESET

    def drop_pheromones(self, path: Path, drop_rate:float = DROPRATE) -> None:
        assert path is not None
        for pheromone in self.pheromones.keys():
            drop_amount = self.pheromones[pheromone]*drop_rate
            self.pheromones[pheromone] -= drop_amount
            path.increase_pheromones(pheromone, drop_amount)
        
          
if __name__ == "__main__":
    node_amount = random.randint(25,50)
    path_amount = random.randint(node_amount,max(min(round(node_amount*1.5),(node_amount*(node_amount-1))//2),node_amount))
    ant_amount = random.randint(node_amount,node_amount*4)
    for i in range(node_amount):
        if i < len(PHEROMONES):
            facility = PHEROMONES[i]
        elif i == len(PHEROMONES):
            facility = "nest"
        else:
            facility = random.choices(population=[*PHEROMONES,"nest",None],
                                      weights=[1 if i != len(PHEROMONES)+1 else node_amount*0.75
                                               for i in range(len(PHEROMONES)+2)])[0]
        nodes[i] = Node(id=i,
                        x=random.random()*(WIDTH-2*MARGIN)+MARGIN,
                        y=random.random()*(HEIGHT-2*MARGIN)+MARGIN,
                        facility=facility,
                        connections=[])
    print("Initiated nodes")
    nests:list[int] = []
    for node in nodes.values():
        if node.facility == "nest":
            nests.append(node.id)
    for i in range(path_amount):
        node1 = random.randint(0, node_amount-1)
        while len(nodes[node1].connections) >= (path_amount/node_amount)*3:
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
            pheromones = initiate_pheromone_dict()
            paths.append(Path(origin=node.id,destination=node2,pheromones=pheromones))
    print("Initiated paths")
    for i in range(ant_amount):
        nest = random.choice(nests)
        ants.append(Ant(origin=nest,goal=nest))
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
            path.evaporate_pheromones()
            path.draw(screen)
        for ant in ants:
            ant.step()
            ant.draw(screen)
        if ants[0].goal is not None: print(ants[0].pheromones)
        cur_path = get_path(ants[0].origin,ants[0].destination)
        if cur_path is not None: print(cur_path.pheromones)
        pygame.display.flip()
        clock.tick(FRAMERATE)
        # print(clock.get_fps())
        
    pygame.quit()
    
# TODO: JSON graphs