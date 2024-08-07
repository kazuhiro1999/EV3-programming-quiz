import cv2
import numpy as np
import time
import json

from face_tracking import FacialTracking
from eventsystem import Event


class EyeBlinkDetector:

    LEFT_EYE_LANDMARKS = [33, 159, 158, 133, 153, 144]
    RIGHT_EYE_LANDMARKS =  [466, 386, 385, 362, 380, 373]

    def __init__(self, 
                 min_eye_blink_interval=0.2,
                 max_detection_interval=1.0,
                 debug=True):

        self.min_eye_blink_interval = min_eye_blink_interval
        self.max_detection_interval = max_detection_interval
        self.debug = debug

        self.on_open = Event()
        self.on_close = Event()
        self.on_blink = Event()
        self.on_update = Event()

        self.eye_ratio = 0
        self.is_open = True
        self.state = "OPEN"
        self.last_close_time = time.time()
        self.load_calibration_data("config.json")
        

    def load_calibration_data(self, filepath):
        with open(filepath, 'r') as f:
            result = json.load(f)

        self.min_eye_openess = result.get("min_eye_openess", 0.1)
        self.max_eye_openess = result.get("max_eye_openess", 0.4)
        self.eye_blink_detection_threshold = result.get("eye_blink_detection_threshold", 0.25)
        self.average_eyeblink_frequency = result.get("average_eyeblink_frequency", 20)


    def bind(self, facial_tracking:FacialTracking):
        self.facial_tracking = facial_tracking
        facial_tracking.on_update.add_listener(self._process)

    def _process(self, frame, face_landmarks):
        # まばたき
        left_eye_ratio = calculate_eye_ratio(face_landmarks, EyeBlinkDetector.LEFT_EYE_LANDMARKS)
        right_eye_ratio = calculate_eye_ratio(face_landmarks, EyeBlinkDetector.RIGHT_EYE_LANDMARKS)
        self.eye_ratio = (left_eye_ratio + right_eye_ratio) / 2

        self.is_open = self.eye_ratio > self.eye_blink_detection_threshold
        self._update_state()
        self.on_update.invoke()

    def _update_state(self):
        # 状態を更新
        if self.is_open and self.state == "CLOSE":
            self.state = "OPEN"
            self.on_open.invoke()
            if time.time() - self.last_close_time < self.max_detection_interval:
                self.on_blink.invoke()
        elif not self.is_open and self.state == "OPEN":
            if time.time() - self.last_close_time > self.min_eye_blink_interval:
                self.state = "CLOSE"
                self.on_close.invoke()
                self.last_close_time = time.time()
        else:
            pass      


def calculate_eye_ratio(face_landmarks, eye_landmarks):
    # 眼のアスペクト比を計算する関数
    eye_points = np.array([[face_landmarks.landmark[i].x, face_landmarks.landmark[i].y] for i in eye_landmarks])
    # EAR計算
    A = np.linalg.norm(eye_points[1] - eye_points[5])
    B = np.linalg.norm(eye_points[2] - eye_points[4])
    C = np.linalg.norm(eye_points[0] - eye_points[3])
    eye_ratio = (A + B) / (2.0 * C)
    return eye_ratio


def calc_iris_min_enc_losingCircle(image, landmarks):
    image_width, image_height = image.shape[1], image.shape[0]
    landmark_point = []

    for index, landmark in enumerate(landmarks.landmark):
        landmark_x = min(int(landmark.x * image_width), image_width - 1)
        landmark_y = min(int(landmark.y * image_height), image_height - 1)

        landmark_point.append((landmark_x, landmark_y))

    left_eye_points = [
        landmark_point[468],
        landmark_point[469],
        landmark_point[470],
        landmark_point[471],
        landmark_point[472],
    ]
    right_eye_points = [
        landmark_point[473],
        landmark_point[474],
        landmark_point[475],
        landmark_point[476],
        landmark_point[477],
    ]

    left_eye_info = calc_min_enc_losingCircle(left_eye_points)
    right_eye_info = calc_min_enc_losingCircle(right_eye_points)

    return left_eye_info, right_eye_info


def calc_min_enc_losingCircle(landmark_list):
    center, radius = cv2.minEnclosingCircle(np.array(landmark_list))
    center = (int(center[0]), int(center[1]))
    radius = int(radius)

    return center, radius
