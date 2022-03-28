import os
import threading
from concurrent.futures import ThreadPoolExecutor
from tools import run_net


class SourceQueue:
    def __init__(self, path, fps):
        self.queue = []
        self.source_url_path = path
        self.fps = fps
        self.lock = threading.Lock()
        self.process_task = None

    def set_task(self, task):
        self.process_task = task

    def put(self, obj):
        with self.lock:
            length = len(self.queue)
            if length == 0:
                index = 0
            else:
                index = length-1
            self.queue.insert(index, obj)

    def get(self, index):
        with self.lock:
            if len(self.queue) == 0 or len(self.queue) <= index:
                return None
            return self.queue.__getitem__(index)

    def iterable(self):
        return self.queue.__iter__()

    def pop(self):
        with self.lock:
            return self.queue.pop()

    def empty(self):
        return len(self.queue) == 0

    def ready(self):
        return self.process_task.done()

    def preparing(self):
        return self.process_task.running()


class SourceManager:
    """
    特别备注，摄像头实时检测几乎会占用所有CPU、内存资源，用完应当及时释放
    """
    def __init__(self):
        #  单线程，机器带不动只能一条一条跑
        self.threadpool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="SlowFast")
        self.source_map = {}

    def get_or_create(self, source, fps):
        if self.source_map.get(source) is not None:
            if source == '0':
                try:
                    self.source_map[source].process_task.cancel()
                except BaseException:
                    return self.source_map[source]
            return self.source_map[source]
        else:
            queue = SourceQueue(source, fps)
        self.source_map[source] = queue

        # 加入计算队列
        args = [source, queue]
        task = self.threadpool.submit(lambda p: run_net.main(*p),args)
        queue.set_task(task)

        return queue
