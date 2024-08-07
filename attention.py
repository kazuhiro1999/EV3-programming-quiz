"""
まばたき等から集中度/覚醒度を推定

"""

import time
import json

from eye_blink import EyeBlinkDetector
from utils import find_first_index


class AttentionEstimator:
    def __init__(self):
        self.eyeblink_buffer_size = 30  # 30秒間の瞬きデータを使用
        self.eyeopen_buffer_size = 10  # 10秒間の目の開閉データを使用
        #self.update_interval = 1  # 1秒ごとにデータを更新

        self.min_eye_openess = 0.1
        self.max_eye_openess = 0.4
        self.eye_blink_detection_threshold = 0.25
        self.average_eyeblink_frequency = 20

        self.timestamps = []  # time seconds when data captured
        self.is_valid = []  # true if user look at PC
        self.eye_openess = []  # eye ratio 0 (closed) ~ 1 (opened)
        self.eyeblink_events = []  # timestamps when eye blink detected

        self.valid_rate = 0
        self.attention_level = 0  # 集中度
        self.arousal = 0  # 覚醒度

        self.eyeblink_detector = None
        self.load_calibration_data("config.json")   
        self.idx = 0     
        self.start_time = time.time()

    def load_calibration_data(self, filepath):
        with open(filepath, 'r') as f:
            result = json.load(f)

        self.min_eye_openess = result.get("min_eye_openess", 0.1)
        self.max_eye_openess = result.get("max_eye_openess", 0.4)
        self.eye_blink_detection_threshold = result.get("eye_blink_detection_threshold", 0.25)
        self.average_eyeblink_frequency = result.get("average_eyeblink_frequency", 20)

    def bind(self, blink_detector:EyeBlinkDetector):
        self.eyeblink_detector = blink_detector        
        self.eyeblink_detector.on_blink.add_listener(self.add_eyeblink_event)
        self.eyeblink_detector.on_update.add_listener(self.capture_data)

    def add_eyeblink_event(self):
        current_time = time.time() - self.start_time
        self.eyeblink_events.append(current_time)

    def capture_data(self):
        current_time = time.time() - self.start_time

        self.timestamps.append(current_time)
        self.eye_openess.append(self.eyeblink_detector.eye_ratio)
        self.is_valid.append(self.eyeblink_detector.facial_tracking.is_facing_forward)
        return

    def update(self):
        if self.eyeblink_detector is None:
            return False
        
        if len(self.timestamps) < 1:
            return False
        
        current_time = time.time() - self.start_time
        self.idx = find_first_index(self.timestamps, current_time - self.eyeopen_buffer_size, last_idx=self.idx)

        # 集中度
        count = sum(map(lambda t: t > current_time - self.eyeblink_buffer_size, self.eyeblink_events))
        freq = count
        if current_time < self.eyeblink_buffer_size:
            freq = count * self.eyeblink_buffer_size / current_time
        attn_level = 12 / max(freq, 1)  # ToDo:改善  freq=20で通常0.6
        attn_level = min(attn_level, 1)

        # 覚醒度
        is_valid = self.is_valid[self.idx:]
        eye_openess = self.eye_openess[self.idx:]
        eye_openess = [value for valid, value in zip(is_valid, eye_openess) if valid]

        valid_rate = sum(self.is_valid[self.idx:]) / max(len(self.is_valid[self.idx:]), 1)
        average_eye_openess = sum(eye_openess) / max(len(eye_openess), 1)
        # ToDo:線形補間 => 改善 & 覚醒度の計算時に有効なものしか使用しない
        arousal = (average_eye_openess - self.min_eye_openess) / (self.max_eye_openess - self.min_eye_openess)
        arousal = min(max(arousal, 0), 1)

        self.valid_rate = valid_rate
        self.attention_level = attn_level
        self.arousal = arousal
        return