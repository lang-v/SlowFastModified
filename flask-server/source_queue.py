import os
import threading
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

import cv2
import simplejson.encoder

from tools import run_net


class SourceState(Enum):
    INIT = 0
    READY = 1
    PREPARING = 2
    ERROR = 3


class SourceQueue:
    def __init__(self, path, info):
        # self.queue = []
        self.output_path = "static/output/"

        self.video_filename = path
        self.video_preds_filename = path + ".json"

        self.video_os = None
        self.video_detect_os = None

        self.video_info = info
        """
        {
            "fps"：10,
            "width": 100
            "height":100
            ...
        }
        """

        # 计算任务
        self.lock = threading.Lock()
        self.process_task = None

        self.state = SourceState.INIT

    def set_task(self, task):
        self.state = SourceState.PREPARING
        self.process_task = task

    def write_frames(self, frames):
        fourcc = cv2.VideoWriter_fourcc(*'MP4V')  # 视频编解码器
        if self.video_os is None:
            self.video_os = cv2.VideoWriter("{}{}".format(self.output_path, self.video_filename),
                                            fourcc, int(self.video_info['fps']),
                                            (int(self.video_info['width']), int(self.video_info['height'])),True)
        for frame in frames:
            self.video_os.write(frame)

    def write_preds_info(self, info):
        """
        Args:
            info:  {"preds":[]}

        Returns:

        """
        total_info = {}
        total_info.update(self.video_info)
        total_info.update({"preds_intime": info})
        print("total_info:{}".format(total_info))
        json = simplejson.encoder.JSONEncoder().encode(total_info)
        print("json:{}".format(json))
        if self.video_detect_os is None:
            self.video_detect_os = open(self.output_path + self.video_preds_filename, "w")
        self.video_detect_os.write(json)

    def flush(self):
        if self.video_os is not None:
            self.video_os.release()
        if self.video_detect_os is not None:
            self.video_detect_os.flush()
            self.video_detect_os.close()
        self.state = SourceState.READY

    # def put(self, obj):
    #     with self.lock:
    #         length = len(self.queue)
    #         if length == 0:
    #             index = 0
    #         else:
    #             index = length - 1
    #         self.queue.insert(index, obj)
    #
    # def get(self, index):
    #     with self.lock:
    #         if len(self.queue) == 0 or len(self.queue) <= index:
    #             return None
    #         return self.queue.__getitem__(index)
    #
    # def iterable(self):
    #     return self.queue.__iter__()
    #
    # def pop(self):
    #     with self.lock:
    #         return self.queue.pop()
    #
    # def empty(self):
    #     return len(self.queue) == 0

def check_computed(path):
    # 判断是否已经计算过了
    real_video = "static/output/{}".format(path)
    real_preds_info = "static/output/{}.json".format(path)
    return os.path.exists(real_video) and os.path.exists(real_preds_info)


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

            queue = self.source_map[source]
            #     重新计算
            if not check_computed(source):
                # 就算是在内存中存在，也可能出现导出的视频文件已经删除了
                args = [source, queue]
                task = self.threadpool.submit(lambda p: run_net.main(*p), args)
                queue.set_task(task)
            else:
                queue.state = SourceState.READY

            return source
        else:
            queue = SourceQueue(source, fps)
        self.source_map[source] = queue

        if not check_computed(source):
            # 加入计算队列
            args = [source, queue]
            task = self.threadpool.submit(lambda p: run_net.main(*p), args)
            queue.set_task(task)
            # run_net.main(source, queue)
        return queue
