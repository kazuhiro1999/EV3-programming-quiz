"""
目のキャリブレーション用プログラム

output:
    min_eye_openess: 目の開閉の最小値（閉じ切った状態）
    max_eye_openess: 目の開閉の最大値（大きく目を開いた状態）
    average_eye_openess: 目の開閉の平均値（通常状態）
    eye_blink_detection_threshold: 瞬き検知のしきい値
    eye_blink_frequency: 1分間のまばたき回数の推定値

"""

import tkinter as tk
import time
import random
import json

from face_tracking import FacialTracking
from eye_blink import EyeBlinkDetector


RADIUS = 20
POINTS = [("UP", 0.0, -0.9), ("DOWN", 0.0, 0.9), ("LEFT", -0.9, 0.0), ("RIGHT", 0.9, 0.0)]  # (id, x, y)  s.t. -1 < x,y < 1 
MOVE_SPEED = 0.5
MOVE_INTERVAL = 1.5


face_tracking = FacialTracking()
face_tracking.start()

blink_detector = EyeBlinkDetector()
blink_detector.bind(face_tracking)


root = tk.Tk()
root.state("zoomed")
root.resizable(False, False)

# Canvasの作成
canvas = tk.Canvas(root, bg="white")
canvas.pack(fill=tk.BOTH, expand=True)

width = root.winfo_screenwidth()
height = root.winfo_screenheight()

center_x = int(width/2)
center_y = int(height/2)

def add_eyeblink_event():
    t = time.time() - start_time
    eye_blink.append(t)

def start(event):
    global start_time
    canvas.delete(label)
    button.destroy()

    blink_detector.on_blink.add_listener(add_eyeblink_event)
    start_time = time.time()

    root.after(1000, update)


label = canvas.create_text(center_x, center_y-128, text="点を目で追え！", font=("Meiryo",32))
circle = canvas.create_oval(center_x - RADIUS, center_y - RADIUS, center_x + RADIUS, center_y + RADIUS, fill="black")
button = tk.Button(root, text='スタート', width=24, font=("Meiryo",32))
button.bind("<Button-1>", start)
button.place(x=center_x, y=center_y+192, anchor=tk.CENTER)

points = POINTS
random.shuffle(points)
points.append(("CENTER", 0, 0))

current_index = 0
current = ("CENTER", 0, 0)
target = ("CENTER", 0, 0)
is_moving = False
start_time = 0
last_time = 0

eye_open = []
eye_blink = []


def update():
    global current_index, last_time, is_moving, current, target

    current_time = time.time() - start_time
    elapsed_time = current_time - last_time
    
    # 目の開き具合
    eye_open.append(blink_detector.eye_ratio)

    if is_moving:
        if elapsed_time > MOVE_SPEED:
            move_circle(1, current, target)
            current = target
            is_moving = False

            if len(points) < 1:
                root.after(1500, on_end)
                return
            
            last_time = current_time
        else:            
            t = elapsed_time / MOVE_SPEED
            move_circle(t, current, target)
    else:
        if elapsed_time >= MOVE_INTERVAL:
            target = points.pop(0)
            print(target[0])
            is_moving = True
            last_time = current_time

    root.after(20, update)


def move_circle(t, current, target):
    _, x1, y1 = current
    _, x2, y2 = target

    x = (1 - t) * x1 + t * x2
    y = (1 - t) * y1 + t * y2

    nx = (1 + x) * center_x
    ny = (1 + y) * center_y

    canvas.coords(circle, [nx - RADIUS, ny - RADIUS, nx + RADIUS, ny + RADIUS])
    return

def on_end():
    print("終了")
    blink_detector.on_blink.remove_listener(add_eyeblink_event)
    face_tracking.stop()
    face_tracking.release()

    # 処理
    avg = sum(eye_open) / len(eye_open)
    print(f"平均の目の開き={avg}")
    print(f"まばたきの回数={len(eye_blink)}")

    result = {
        'min_eye_openess': min(eye_open),
        'max_eye_openess': max(eye_open),
        'average_eye_openess': sum(eye_open) / len(eye_open),
        'eye_blink_detection_threshold': (avg + min(eye_open)) / 2,  # 瞬き検知のしきい値
        'eye_blink_frequency': len(eye_blink) * 5  # 1分間にどれだけまばたきをするか このタスクは12秒で実行
    }

    with open("config.json", 'w') as f:
        json.dump(result, f, indent=4)

    # 終了
    canvas.delete(circle)
    label = canvas.create_text(center_x, center_y, text="キャリブレーション完了", font=("Meiryo",32))
    return


root.mainloop()