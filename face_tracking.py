"""
mediapipeを使った顔のキーポイント検出
非同期で実行
"""

import cv2
import threading
import mediapipe as mp

from utils import *
from eventsystem import Event


class FacialTracking:
    def __init__(self, src=0):
        self.capture = cv2.VideoCapture(src)
        self.frame = None
        self.running = False
        self.lock = threading.Lock()
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )        
        self.face_landmarks = None
        self.left_eye = None
        self.right_eye = None
        self.head_position = np.zeros(3)
        self.head_direction = np.zeros(3)
        self.is_facing_forward = False
        self.on_update = Event()

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._process)
            self.thread.start()

    def _process(self):
        while self.running:
            ret, frame = self.capture.read()
            if ret:
                with self.lock:
                    self.frame = frame
                
                results = self.face_mesh.process(frame)

                if results.multi_face_landmarks is None:
                    # 検出失敗
                    self.is_facing_forward = False
                else:
                    face_landmarks = results.multi_face_landmarks[0]
                    
                    # 虹彩の外接円の計算
                    left_eye, right_eye = None, None
                    left_eye, right_eye = calc_iris_min_enc_losingCircle(
                        frame,
                        face_landmarks,
                    )

                    self.head_position = calculate_head_position(face_landmarks)
                    self.head_direction = calculate_head_direction(face_landmarks)
                    self.is_facing_forward = is_facing_forward(self.head_direction)

                    with self.lock:
                        self.face_landmarks = face_landmarks
                        self.left_eye = left_eye
                        self.right_eye = right_eye
                
                self.on_update.invoke(frame, self.face_landmarks)

            #time.sleep(0.01)  

    def read(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def stop(self):
        self.running = False
        self.thread.join()

    def release(self):
        if self.running:
            self.stop()
        self.capture.release()



FORWARD = np.array([0, 0, -1])

def calculate_head_position(face_landmarks):
    # キーポイント
    nose_top = np.array([-face_landmarks.landmark[1].x, -face_landmarks.landmark[1].y, face_landmarks.landmark[1].z])
    left_edge = np.array([-face_landmarks.landmark[361].x, -face_landmarks.landmark[361].y, face_landmarks.landmark[361].z])
    right_edge = np.array([-face_landmarks.landmark[132].x, -face_landmarks.landmark[132].y, face_landmarks.landmark[132].z])

    # 重心計算
    head_position = (nose_top + left_edge + right_edge) / 3

    return head_position


def calculate_head_direction(face_landmarks):
    # キーポイント
    nose_top = np.array([-face_landmarks.landmark[1].x, -face_landmarks.landmark[1].y, face_landmarks.landmark[1].z])
    left_edge = np.array([-face_landmarks.landmark[361].x, -face_landmarks.landmark[361].y, face_landmarks.landmark[361].z])
    right_edge = np.array([-face_landmarks.landmark[132].x, -face_landmarks.landmark[132].y, face_landmarks.landmark[132].z])

    # 向き計算
    direction = nose_top - (left_edge + right_edge) / 2
    direction = direction / np.linalg.norm(direction)

    return direction


def is_facing_forward(direction, threshold=30):
    # 内積を用いて方向ベクトルと前方向ベクトルの角度を計算
    dot_product = np.dot(direction, FORWARD)
    angle = np.arccos(dot_product) * 180 / np.pi

    return angle <= threshold