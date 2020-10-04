import threading
import traceback
import time

from queue import Queue

import settings


class Dispatcher(threading.Thread):
    def __init__(self):
        super(Dispatcher, self).__init__()
        self.queue = Queue(settings.MAX_QUEUQ)
        self.terminate = False

    def run(self):
        while not self.terminate:
            try:
                if len(threading.enumerate()) < settings.MAX_TREADS + 2 and \
                        not self.queue.empty():
                    task = self.queue.get()
                    task.start()
            except Exception as exc:
                print(exc)
                traceback.print_exc()
            finally:
                time.sleep(settings.DISPATCHER_SLEEP)

    def put(self, item):
        self.queue.put(item)
