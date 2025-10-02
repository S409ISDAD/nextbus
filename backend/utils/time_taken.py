import time
import logging

log = logging.getLogger(__name__)


class time_taken:
    def __init__(self, name=None, threshold=0):
        self.name = name
        self.threshold = threshold

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, *args):
        taken = time.time() - self.start
        if self.threshold and taken > self.threshold:
            if self.name:
                log.debug(
                    f"Time taken for {self.name}: {time.time() - self.start:.3f}s"
                )
            else:
                log.debug(f"Time taken: {time.time() - self.start:.3f}s")
