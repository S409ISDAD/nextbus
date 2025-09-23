import time
import logging

log = logging.getLogger(__name__)


class time_taken:
    def __init__(self, name=None):
        self.name = name

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, *args):
        if self.name:
            log.debug(f"Time taken for {self.name}: {time.time() - self.start:.3f}s")
        else:
            log.debug(f"Time taken: {time.time() - self.start:.3f}s")
