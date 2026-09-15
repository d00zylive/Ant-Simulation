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

    def increase_pheromones(self) -> None:
        pass

    def decay_pheromones(self) -> None:
        pass


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