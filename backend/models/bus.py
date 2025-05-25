class Bus:
    def __init__(
        self,
        service,
        destination,
        reg,
        fleet_num,
        journey_id,
        times,
        delay,
        lateness,
        # speed,
        progress,
        coords,
        timestamp,
    ):
        self.service: str = service  # bus number e.g. 64
        self.destination: str = destination
        self.reg: str = reg  # vehicle license plate
        self.fleet_num: str = fleet_num
        self.journey_id: int = journey_id
        self.delay: int = delay  # how many seconds behind/ahead e.g. 120 = 2 min late, -60 = 1 min early
        self.lateness: str = lateness  # text to display how late or early it is
        self.expected: int = times[
            "expected"
        ]  # expected arrival time at stop (unix timestamp)
        self.scheduled: int = times[
            "scheduled"
        ]  # scheduled arrival time at stop (unix timestamp)
        self.started: bool = not (times["not_started"])
        # self.speed: float = speed  # how fast the bus is going
        self.progress: float = progress  # progress between 2 stops, 0-1
        self.coords: list[float] = coords
        self.timestamp: int = timestamp  # time when the data was fetched, indicates age
