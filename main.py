class Node:
    id: int
    x: float
    y: float
    facility: str|None
    paths: list[int]


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


class Ant:
    origin: int
    destination: int
    distance: float
    nest: int
    needs: dict[str,float]
    pheromones: dict[str,float]

    def step(self) -> None:
        pass

    def choose_path(self) -> int:
        pass

    def get_highest_need(self) -> str:
        pass

    def utilise_facility(self) -> None:
        pass

    def drop_pheromones(self) -> None:
        pass