"""
ev3プログラムの解析用コード
"""


import ast
from io import StringIO
import sys
import random
import threading
import traceback
from enum import Enum
from unittest.mock import Mock, MagicMock


# 列挙型

class Port(Enum):
    A = 0
    B = 1
    C = 2
    D = 3
    S1 = 4
    S2 = 5
    S3 = 6
    S4 = 7

class Direction(Enum):
    CLOCKWISE = 1
    COUNTERCLOCKWISE = -1

class Stop(Enum):
    COAST = 0
    BRAKE = 1
    HOLD = 2

class Color(Enum):
    BLACK = 1
    BLUE = 2
    GREEN = 3
    YELLOW = 4
    RED = 5
    WHITE = 6
    BROWN = 7

class Button(Enum):
    LEFT_UP = 1
    LEFT_DOWN = 2
    RIGHT_UP = 3
    RIGHT_DOWN = 4
    BEACON = 5


# モーター
class Motor:
    def __init__(self, port, positive_direction=Direction.CLOCKWISE, gears=None):
        self.port = port
        self.positive_direction = positive_direction
        self.gears = gears
        self.speed = MagicMock(return_value=0)
        self.angle = MagicMock(return_value=0)
        self.reset_angle = MagicMock()
        self.stop = MagicMock()
        self.brake = MagicMock()
        self.hold = MagicMock()
        self.run = MagicMock()
        self.run_time = MagicMock()
        self.run_angle = MagicMock()
        self.run_until_stalled = MagicMock(return_value=0)
        self.dc = MagicMock()
        self.track_target = MagicMock()
        self.control = MagicMock()
    def run_target(self):
        pass

# センサー系
class TouchSensor:
    def __init__(self, port):
        self.port = port
    def pressed(self):
        return random.choice([True, False])

class ColorSensor:
    def __init__(self, port):
        self.port = port
        self.ambient = MagicMock(return_value=0)
        self.rgb = MagicMock(return_value=(0, 0, 0))
    def color(self):
        return random.choice(list(Color))
    def reflection(self):
        return random.uniform(0, 100)

class InfraredSensor:
    def __init__(self, port):
        self.port = port
        self.distance = MagicMock(return_value=0)
        self.beacon = MagicMock(return_value=(None, None))
        self.buttons = MagicMock(return_value=[])
        self.keypad = MagicMock(return_value=[])

class UltrasonicSensor:
    def __init__(self, port):
        self.port = port
        self.presence = MagicMock(return_value=False)
    def distance(self):
        return random.uniform(0, 255)

class GyroSensor:
    def __init__(self, port, positive_direction=Direction.CLOCKWISE):
        self.port = port
        self.positive_direction = positive_direction
        self.speed = MagicMock(return_value=0)
        self.angle = MagicMock(return_value=0)
        self.reset_angle = MagicMock()

# ロボティクス
class DriveBase:
    def __init__(self, left_motor, right_motor, wheel_diameter, axle_track):
        self.straight = MagicMock()
        self.turn = MagicMock()
        self.settings = MagicMock()
        self.distance = MagicMock(return_value=0)
        self.angle = MagicMock(return_value=0)
        self.state = MagicMock(return_value=(0, 0, 0, 0))
        self.reset = MagicMock()
    def drive(self, speed=100, turn_rate=0):
        pass
    def drive_time(self, speed, steering, time):
        pass
    def stop(self, stop_type=Stop.COAST):
        pass

# ev3dev2 のモジュールをモック
sys.modules['pybricks'] = Mock()

sys.modules['pybricks.parameters'] = Mock()
sys.modules['pybricks.parameters'].Port = Port
sys.modules['pybricks.parameters'].Direction = Direction
sys.modules['pybricks.parameters'].Stop = Stop
sys.modules['pybricks.parameters'].Color = Color
sys.modules['pybricks.parameters'].Button = Button

sys.modules['pybricks.ev3devices'] = Mock()
sys.modules['pybricks.ev3devices'].Motor = Motor
sys.modules['pybricks.ev3devices'].TouchSensor = TouchSensor
sys.modules['pybricks.ev3devices'].ColorSensor = ColorSensor
sys.modules['pybricks.ev3devices'].InfraredSensor = InfraredSensor
sys.modules['pybricks.ev3devices'].UltrasonicSensor = UltrasonicSensor
sys.modules['pybricks.ev3devices'].GyroSensor = GyroSensor

sys.modules['pybricks.robotics'] = Mock()
sys.modules['pybricks.robotics'].DriveBase = DriveBase


def run_code_in_thread(code, result):
    try:
        exec(code, result)
        result['success'] = True
        result['message'] = "Code executed without errors"
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        line_number = tb[-1].lineno if tb else -1
        print(line_number)
        result['success'] = False
        result['message'] = f"{type(e).__name__}: {e}"
        result['line'] = line_number


def execute_code(code, result):
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    global line
    line = -1
    try:
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    line = node.lineno
        except SyntaxError as e:
            error_msg = f"SyntaxError: {str(e)}"
            result['success'] = False
            result['line_number'] = e.lineno
            result['message'] = error_msg
            return
                
        exec(code, {})
        result['success'] = True
        result['line_number'] = -1
        result['message'] = "Code executed without errors"
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        result['success'] = False
        result['line_number'] = line
        result['message'] = error_msg
    finally:
        sys.stdout = old_stdout
        #print(redirected_output.getvalue())


def check_runtime_errors_with_mock(code, timeout=3.0):
    result = {}
    #thread = threading.Thread(target=run_code_in_thread, args=(code, result))
    thread = threading.Thread(target=execute_code, args=(code, result))
    thread.start()
    thread.join(timeout)
    
    if thread.is_alive():
        return False, "Timed out.", -1
    
    return result.get('success', False), result.get('message', "Unknown error"), result.get('line_number', -1)


if __name__ == "__main__":
    
    test_code = "from pybricks.robotics import DriveBase\n\nrobot = DriveBase(None, None, 56, 120)\nrobot.drive()"
    
    is_valid, message = check_runtime_errors_with_mock(test_code)
    print(message)