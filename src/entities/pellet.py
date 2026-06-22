# pellet.py — dots and power pellets


class Pacgum:
    POINTS: int = 10  # overridden at spawn

    def __init__(self, row: int, col: int) -> None:
        self.row = row
        self.col = col
        self.eaten: bool = False

    def eat(self) -> int:
        if self.eaten:
            return 0
        self.eaten = True
        return self.POINTS


class SuperPacgum:
    POINTS: int = 50
    BLINK_INTERVAL: float = 0.4  # blink every 400ms

    def __init__(self, row: int, col: int) -> None:
        self.row = row
        self.col = col
        self.eaten: bool = False
        self._blink_timer: float = 0.0
        self._visible: bool = True

    @property
    def visible(self) -> bool:
        return self._visible

    def update(self, dt: float) -> None:
        if self.eaten:
            return
        self._blink_timer += dt
        if self._blink_timer >= self.BLINK_INTERVAL:
            self._blink_timer = 0.0
            self._visible = not self._visible

    def eat(self) -> int:
        if self.eaten:
            return 0
        self.eaten = True
        self._visible = False
        return self.POINTS
