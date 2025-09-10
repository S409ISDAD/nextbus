from pydantic import BaseModel


class Progress(BaseModel):
    sequence: int  # index of the stop it has just passed
    next_stop: str  # id of the next stop
    prev_stop: str  # id of the stop it just passed
    progress: float  # float 0-1 of completion from prev stop to next
