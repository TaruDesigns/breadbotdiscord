from settings import SETTINGS


class Registry:
    def __init__(self) -> None:
        self.settings = SETTINGS


REGISTRY = Registry()
