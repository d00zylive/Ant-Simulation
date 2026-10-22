import math
import random
import pygame
import json
import os

PHEROMONES: list[str] = ["store"]

def initiate_pheromone_dict(value:float = 0, nest:int|None = None) -> dict[str|int,float]:
    pheromones:dict[str|int,float] = {}
    for pheromone in PHEROMONES:
        pheromones[pheromone] = value
    if nest is not None:
        pheromones[nest] = value
    return pheromones

FRAMERATE = 60
WIDTH,HEIGHT = 1920,900
MARGIN = 10
NODECOLOURS:dict[str|None,pygame.typing.ColorLike] = {
    None: (0,0,0),
    "store": (0,255,0),
    "nest": (255,0,0)
}
FACILITYRADIUS = 7
NODERADIUS = 2
path_colour_ramp = 1
PATHWIDTH = 2
ANTCOLOUR = (0,0,255)
ANTSIZE = 8


GENERATEGRAPH = False
GRAPHFILE = os.path.join(os.path.dirname(__file__),"export.json")
ANTSPERNEST = (0,5)

SIMSPEED = 1
ANTSPEED = 0.0001*SIMSPEED/FRAMERATE # degrees per second
WANDERCHANCE = 0.005 # chance for every node to ignore pheromones
REVERSEMODIFIER = 0
RETAINRATE = 0.995 # factor per meter (only accurate around the equator)
NEEDGROWTH = 1 # need (arbitrary number) gain per second
PHEROMONERESET = 5 # the amount of pheromones an ant gets from using a facility 
EVAPORATIONRATE = 0.995**(1*SIMSPEED/FRAMERATE) # the factor of pheromones that evaporate every second

nodes: dict[int, Node] = {}
paths: dict[tuple[int,int],Path] = {}
ants: list[Ant] = []
nests: list[int] = []

class Path:
    origin: int
    destination: int
    pheromones: dict[str|int,float]
    origin_pos: tuple[float,float]|None
    destination_pos: tuple[float,float]|None
    
    def __init__(self, origin: int, destination: int, pheromones:dict[str|int,float]|None = None):
        self.origin = origin
        self.destination = destination
        self.pheromones = pheromones if pheromones is not None else initiate_pheromone_dict()
        self.origin_pos = None
        self.destination_pos = None
        
    def __repr__(self):
        return f"Path(origin={self.origin},destination={self.destination},pheromones={self.pheromones})"
    
    def __str__(self):
        return f"Path(origin={nodes[self.origin]},destination={nodes[self.destination]},pheromones={self.pheromones})"
     
    def fetch_origin(self) -> tuple[float,float]:
        if self.origin_pos is None:
            self.origin_pos = (nodes[self.origin].x, nodes[self.origin].y)
        return self.origin_pos
    
    def fetch_destination(self) -> tuple[float,float]:
        if self.destination_pos is None:
            self.destination_pos = nodes[self.destination].x, nodes[self.destination].y
        return self.destination_pos
        
    def draw(self, surface: pygame.Surface, origin:tuple[float,float] = (0,0), scale:float = 1) -> None:
        start = self.fetch_origin()
        end = self.fetch_destination()
        ramp = lambda x: round(255-(1/(path_colour_ramp*(x+1/(path_colour_ramp*255))))) if x != 0 else 0 #lambda x: min(x/(self.get_length()*10),255)#
        nest_pheromone_sum = 0#ramp(sum(self.pheromones[pheromone] if isinstance(pheromone,int) else 0 for pheromone in self.pheromones.keys())) # DOUBLES DRAWTIME
        #pygame.draw.line(surface, color=(round(nest_pheromone_sum),round(ramp(self.pheromones["store"])),0), start_pos=((start[0]-origin[0])*scale,surface.get_height()-(start[1]-origin[1])*scale), end_pos=((end[0]-origin[0])*scale,surface.get_height()-(end[1]-origin[1])*scale), width=PATHWIDTH)

    def get_pheromone(self, type: str|int) -> float:
        if type in self.pheromones.keys():
            return self.pheromones[type]
        else:
            return 0

    def increase_pheromones(self, type: str|int, amount: float) -> None:
        if type not in self.pheromones.keys():
            self.pheromones[type] = amount
        else:
            self.pheromones[type] += amount
        
    def evaporate_pheromones(self, rate:float = EVAPORATIONRATE) -> None:
        for key in self.pheromones.keys():
            self.pheromones[key] *= rate
            
    def get_length(self) -> float:
        origin_node, destination_node = self.origin_pos if self.origin_pos is not None else self.fetch_origin(), self.destination_pos if self.destination_pos is not None else self.fetch_destination()
        return math.sqrt((origin_node[0]-destination_node[0])**2+(origin_node[1]-destination_node[1])**2)

def get_path(node1: int, node2: int) -> Path|None:
    if (node1,node2) in paths.keys():
        return paths[(node1,node2)]
    elif (node2,node1) in paths.keys():
        return paths[(node2,node1)]
    else:
        print("Warning: path between {node1} and {node2} doesn't exist, returning None")
        return None

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
    
    def draw(self, surface: pygame.Surface, origin:tuple[float,float] = (0,0), scale:float = 1):
        radius = NODERADIUS if self.facility is None else FACILITYRADIUS
        if self.facility is not None:
            pygame.draw.circle(surface=surface, color=NODECOLOURS[self.facility],center=((self.x-origin[0])*scale,surface.get_height()-(self.y-origin[1])*scale),radius=radius)
    
    def get_paths(self) -> list[Path]:
        path_objects: list[Path] = []
        for connection in self.connections:
            path = get_path(self.id, connection)
            if path is None:
                print(f"WARNING: no path between {self} and {nodes[connection]}. Creating new entry.")
                path = Path(origin=self.id, destination=connection, pheromones=initiate_pheromone_dict())
                paths[(self.id,connection)] = path
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
        self.pheromones[self.nest] = PHEROMONERESET
        self.goal = goal
        
    def __repr__(self):
        return f"Ant(origin={self.origin},destination={self.destination},distance={self.distance},nest={self.nest},needs={self.needs},pheromones={self.pheromones},goal={self.goal})"
    
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
    
    def draw(self, surface: pygame.Surface, origin:tuple[float,float] = (0,0), scale:float = 1):
        x,y = self.get_pos()
        pygame.draw.rect(surface,color=(255 if isinstance(self.goal,int) else 0, 255 if self.goal=="store" else 0, 255),rect=pygame.Rect(((x-origin[0])*scale-ANTSIZE/2),surface.get_height()-((y-origin[1])*scale+ANTSIZE/2),ANTSIZE,ANTSIZE))

    def step(self, speed:float = ANTSPEED) -> None:
        for need in self.needs.keys():
            self.needs[need] += NEEDGROWTH
                
        if self.goal is None:
            self.goal = self.get_highest_need()
            
        self.distance += speed
        path = get_path(self.origin, self.destination)
        if path is None:
            self.choose_destination()
            path = get_path(self.origin, self.destination)
            assert path is not None
        while self.distance >= path.get_length():
            if self.goal is not None and (self.destination == self.goal or nodes[self.destination].facility == self.goal) and self.needs[self.goal] > 0:
                self.utilise_facility(self.destination)
            else:
                self.distance -= path.get_length()
                previous_node = self.origin if self.goal != nodes[self.destination].facility and self.goal != self.destination else None
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
        if random.random() >= WANDERCHANCE:
            path_weights: list[float] = []
            for path in connected_paths:
                if path is not None:
                    pheromone_amount = path.get_pheromone(need)/path.get_length()
                    if pheromone_amount != 0 and (previous_node is None or (previous_node != path.origin and previous_node != path.destination)):
                        path_weights.append(pheromone_amount)
                    else:
                        path_weights.append(0)
                else:
                    path_weights.append(0)
            if sum(path_weights) > 0:
                chosen_path: Path|None = random.choices(connected_paths, weights=path_weights)[0]
            else:
                if len(connected_paths) > 1 and previous_node is not None:
                    previous_path = get_path(self.origin, previous_node)
                    assert previous_path is not None
                    connected_paths.remove(previous_path)
                chosen_path: Path|None = random.choice(connected_paths)
        else:
            chosen_path: Path|None = random.choice(connected_paths)
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
            self.needs[facility] = 0
            self.pheromones[facility] = PHEROMONERESET
        else:
            assert node == self.nest
            self.needs[self.nest] = 0
            self.pheromones[self.nest] = PHEROMONERESET

    def drop_pheromones(self, path: Path, retain_rate:float = RETAINRATE) -> None:
        assert path is not None
        for pheromone in self.pheromones.keys():
            drop_amount = self.pheromones[pheromone]*(1-retain_rate**((path.get_length()*40075017)/360))
            self.pheromones[pheromone] -= drop_amount
            path.increase_pheromones(pheromone, drop_amount)
        
def write_json(file_path: str, nodes: list[Node], paths:list[Path]|None = None, ants:list[Ant]|None = None) -> None:
    dump: dict[str,list[dict]] = {}
    dump["nodes"] = [{"id":node.id,"x":node.x,"y":node.y,"facility":node.facility,"connections":node.connections} for node in nodes]
    if paths is not None:
        dump["paths"] = [{"origin":path.origin,"destination":path.destination,"pheromones":path.pheromones} for path in paths]
    if ants is not None:
        dump["ants"] = [{"origin":ant.origin,"destination":ant.destination,"distance":ant.destination,"nest":ant.nest,"needs":ant.needs,"pheromones":ant.pheromones,"goal":ant.goal} for ant in ants]
    try:
        with open(file_path, "x") as f:
            json.dump(dump, f, indent=4)
    except FileExistsError:
        if input("File already exists. Are you sure you want to overwrite? (y/N) ") == "y":
            with open(file_path, "w") as f:
                json.dump(dump, f, indent=2)

def load_json(file_path: str, ignore_paths:bool = False, ignore_ants:bool = False) -> tuple[dict[int,Node],tuple[float,float,float,float]|None]:
    with open(file_path, "r") as f:
        graph = json.load(f)
        
    bounds: tuple[float,float,float,float]|None = tuple([graph["bounds"][key] for key in ["minlat","minlon","maxlat","maxlon"]]) if "bounds" in graph.keys() else None
    
    nodes:dict[int,Node] = {node["id"]:Node(id=node["id"],x=node["x"],y=node["y"],facility=node["facility"],connections=node["connections"]) for node in graph["nodes"]}
        
    return nodes,bounds
          
if __name__ == "__main__":
    if GENERATEGRAPH:
        node_amount = random.randint(100,200)
        path_amount = random.randint(node_amount,max(min(round(node_amount*1.5),(node_amount*(node_amount-1))//2),node_amount))
        for i in range(node_amount):
            if i < len(PHEROMONES):
                facility = PHEROMONES[i]
            elif i == len(PHEROMONES):
                facility = "nest"
            else:
                facility = random.choices(population=[*PHEROMONES,"nest",None],
                                        weights=[1 if i != len(PHEROMONES)+1 else node_amount*0.5
                                                for i in range(len(PHEROMONES)+2)])[0]
            nodes[i] = Node(id=i,
                            x=random.random()*(WIDTH-2*MARGIN)+MARGIN,
                            y=random.random()*(HEIGHT-2*MARGIN)+MARGIN,
                            facility=facility,
                            connections=[])
        print("Initiated nodes")
        for node in nodes.values():
            if node.facility == "nest":
                nests.append(node.id)
        print("Collected nests")
        for i in range(path_amount):
            node1 = random.randint(0, node_amount-1)
            while len(nodes[node1].connections) >= (path_amount/node_amount)*3:
                node1 = random.randint(0, node_amount-1)
            node2 = random.randint(0, node_amount-1)
            while node1 == node2 or node2 in nodes[node1].connections:
                node2 = random.randint(0, node_amount-1)
            nodes[node1].connections.append(node2)
            nodes[node2].connections.append(node1)
            paths[(node1,node2)] = Path(origin=node1,destination=node2)
        for node in nodes.values():
            if len(node.connections) == 0:
                node2 = random.randint(0, node_amount-1)
                while node.id == node2:
                    node2 = random.randint(0, node_amount-1)
                node.connections.append(node2)
                nodes[node2].connections.append(node.id)
                pheromones = initiate_pheromone_dict()
                paths[(node.id,node2)] = Path(origin=node.id,destination=node2,pheromones=pheromones)
        print("Initiated paths")
        for nest in nests:
            for _ in range(random.randint(*ANTSPERNEST)):
                ants.append(Ant(origin=nest))
        print("Initiated ants")
    else:
        nodes,bounds = load_json(GRAPHFILE, ignore_paths=True, ignore_ants=True)
        print("Loaded json")
        for node in nodes.values():
            if node.facility == "nest":
                nests.append(node.id)
        print("Collected nests")
        completed_nodes: list[int] = []
        for node in nodes.values():
            for connection in node.connections:
                if connection not in completed_nodes:
                    paths[(node.id,connection)] = Path(origin=node.id,destination=connection)
            completed_nodes.append(node.id)
        print("Initiated paths")
        for nest in nests:
            for _ in range(random.randint(*ANTSPERNEST)):
                ants.append(Ant(origin=nest))
        print("Initiated ants")
    pygame.init()
    if bounds is None or GENERATEGRAPH:
        screen = pygame.display.set_mode((WIDTH,HEIGHT))
        origin = (0,0)
        scale = 1
    else:
        bounds_ratio = (bounds[3]-bounds[1])/(bounds[2]-bounds[0])
        if bounds_ratio > WIDTH/HEIGHT:
            screen = pygame.display.set_mode((WIDTH,WIDTH/bounds_ratio))
            scale = (WIDTH-MARGIN*2)/(bounds[3]-bounds[1])
        else:
            screen = pygame.display.set_mode((HEIGHT*bounds_ratio,HEIGHT))
            scale = (HEIGHT-MARGIN*2)/(bounds[2]-bounds[0])
        origin = (bounds[1]+(MARGIN/scale),bounds[0]+(MARGIN/scale))
    clock = pygame.time.Clock()
    running = True
    frames = 0
    while running and frames < 1000:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    path_colour_ramp*=1.1
                    print(path_colour_ramp)
                elif event.key == pygame.K_DOWN:
                    path_colour_ramp*=(10/11)
                    print(path_colour_ramp)
        screen.fill((255,255,255))
        
        for node in nodes.values():
            node.draw(screen, origin=origin, scale=scale)
        for path in paths.values():
            path.evaporate_pheromones()
            path.draw(screen, origin=origin, scale=scale)
        for ant in ants:
            ant.step()
            ant.draw(screen, origin=origin, scale=scale)
        pygame.display.flip()
        clock.tick(FRAMERATE)
        print(clock.get_fps())
        frames += 1
    
    pygame.quit()
    if GENERATEGRAPH:
        write_json(os.path.join(os.path.dirname(__file__), GRAPHFILE), nodes=list(nodes.values()))#, paths=paths, ants=ants)