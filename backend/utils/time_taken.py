import time


class time_taken:
    def __enter__(self):
        self.start = time.time()

    def __exit__(self, *args):
        print(f"Time taken: {time.time() - self.start:.3f}s")
