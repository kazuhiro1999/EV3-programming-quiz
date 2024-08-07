"""
顔画像を使用した集中度推定のデモ
localhost:5000で確認できる
"""

import cv2
import threading
from pygame import mixer
from flask import Flask, render_template, Response

from face_tracking import FacialTracking
from eye_blink import EyeBlinkDetector
from attention import AttentionEstimator
from utils import *


app = Flask(__name__)

mixer.init()
sound = mixer.Sound("src/sfx.mp3")
alert = mixer.Sound("src/alert.mp3")

face_tracking = FacialTracking()
face_tracking.start()

blink_detector = EyeBlinkDetector()
blink_detector.bind(face_tracking)

blink_detector.on_blink.add_listener(sound.play)

estimator = AttentionEstimator()
estimator.bind(blink_detector)



def update_frames():
    while True:
        debug_image = face_tracking.frame
        
        # 描画
        if face_tracking.face_landmarks is not None:
            debug_image = draw_landmarks(
                debug_image,
                face_tracking.face_landmarks,
                face_tracking.left_eye,
                face_tracking.right_eye,
            )

        if face_tracking.is_facing_forward:
            debug_image = draw_border(debug_image, color=(0, 255, 0), thickness=5)
        else:
            debug_image = draw_border(debug_image, color=(0, 0, 255), thickness=5)
        
        # フレームをJPEG形式にエンコード
        ret, buffer = cv2.imencode('.jpg', debug_image)
        frame = buffer.tobytes()

        # フレームをストリームとして返す
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_image')
def get_image():
    return Response(update_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/end')
def end():
    global is_running
    #os.kill(os.getpid(), signal.SIGTERM)
    is_running = False
    return "Server shutting down..."

def start_flask_app():
    app.run(debug=True, use_reloader=False)

flask_thread = threading.Thread(target=start_flask_app, daemon=True)
flask_thread.start()

print("Server started.")

is_running = True
valid_rate = []
attention_level = []
arousal = []

try:
    while is_running:
        estimator.update()

        print(f"valid={estimator.valid_rate:.2f}, attn={estimator.attention_level:.3f}, arousal={estimator.arousal:.3f}")

        valid_rate.append(estimator.valid_rate)
        attention_level.append(estimator.attention_level)
        arousal.append(estimator.arousal)

        cv2.waitKey(1000)
except KeyboardInterrupt:
    pass

face_tracking.stop()
face_tracking.release()


from datetime import datetime
import matplotlib.pyplot as plt

plt.figure()
plt.plot(valid_rate, label="valid rate")
plt.plot(attention_level, label="attention level")
plt.plot(arousal, label="arousal")
plt.legend()
plt.savefig(f'./data/{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')