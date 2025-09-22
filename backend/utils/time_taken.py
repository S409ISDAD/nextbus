import time
import logging

log = logging.getLogger(__name__)

class time_taken:
    def __enter__(self):
        self.start = time.time()

    def __exit__(self, *args):
        log.debug(f"Time taken: {time.time() - self.start:.3f}s")
