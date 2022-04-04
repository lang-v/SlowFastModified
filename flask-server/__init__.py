import os.path
import time
from datetime import datetime

import cv2
import flask
from flask_rangerequest import RangeRequest
from flask import Flask, Response, request, send_from_directory, abort, send_file, render_template

from source_queue import SourceManager

app = Flask(__name__)
source_manager = SourceManager()
FPS = 30


#
# def frame_gen(queue):
#     current_index = 0
#     while True:
#         # 限定帧率
#         time.sleep(1 / queue.fps)
#         # 数据未就绪
#         if not (queue.ready() or queue.preparing()):
#             img = cv2.imread("resource/loading.png")
#             res, image = cv2.imencode('.png', img)
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + image.tobytes() + b'\r\n')
#             continue
#
#         # # 此时数据已准备就绪但是内容为空，未知错误.
#         # if queue.empty():
#         #     img = cv2.imread("resource/error.png")
#         #     res, image = cv2.imencode('.png', img)
#         #     # 直接结束请求
#         #     yield (b'--frame\r\n'
#         #            b'Content-Type: image/jpeg\r\n\r\n' + image.tobytes() + b'\r\n')
#         #     return
#
#         # 数据就绪，直接读
#         result = queue.get(current_index)
#         current_index += 1
#
#         if result is None:
#             if queue.preparing():
#                 current_index -= 1
#                 img = cv2.imread("resource/loading.png")
#                 res, image = cv2.imencode('.png', img)
#                 yield (b'--frame\r\n'
#                        b'Content-Type: image/jpeg\r\n\r\n' + image.tobytes() + b'\r\n')
#                 continue
#
#             img = cv2.imread("resource/end.png")
#             res, image = cv2.imencode('.png', img)
#             # 直接结束请求
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + image.tobytes() + b'\r\n')
#             return
#
#         res, image = cv2.imencode('.jpg', result)
#         frame = image.tobytes()
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
#
#
# @app.route("/video_feed", methods=['post', 'get'])
# def index():
#     if request.method == 'POST':
#         source_path = request.form.get("source")
#     else:
#         source_path = request.args.get("source")
#
#     if not source_path.__eq__('0'):
#         if not os.path.exists(source_path):
#             return Response(response='File not found', status='404')
#         cap = cv2.VideoCapture(source_path)
#         fps = cap.get(cv2.CAP_PROP_FPS)
#         cap.release()
#     else:
#         fps = 12
#     print("<video info> fps:{};load in {}".format(fps,source_path))
#     queue = source_manager.get_or_create(source_path, fps)
#     return Response(frame_gen(queue), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/detect", methods=['get', 'post'])
def detect():
    if request.method == 'POST':
        source_path = request.form.get("source")
    else:
        source_path = request.args.get("source")

    source_path = source_path
    if not os.path.exists("input/"+source_path):
        abort(404)
    cap = cv2.VideoCapture("input/"+source_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    display_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    display_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    info = {
        "fps": fps,
        "width": display_width,
        "height": display_height
    }
    print("<video info> fps:{};load in {}".format(12, source_path))
    queue = source_manager.get_or_create(source_path, info)
    print(queue)
    print(queue.state)

    return {
        "info": info,
        "state": queue.state.name,
        "data": {
            "video_path": queue.video_filename,
            "video_preds": queue.video_preds_filename
        }
    }


@app.route("/video", methods=['get', 'post'])
def video():
    if request.method == 'POST':
        source_path = request.form.get("source")
    else:
        source_path = request.args.get("source")

    file = "output/{}".format(source_path)
    if os.path.isfile(file):
        return send_from_directory("output/",source_path)
        # return render_template("video_play.html", source=file)

    abort(404)


if __name__ == '__main__':
    app.run("127.0.0.1", port=8082, threaded=True)
