"""
PC-EV3間のBluetooth通信
"""

import socket
import sys
import time

message = None

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(('169.254.160.72', 50010))  # your PC's Bluetooth IP & PORT
    s.listen(1)
    print('Start program...')
    while True:
        conn, addr = s.accept()
        with conn:
            while True:
                message = conn.recv(1024)
                if message is not None:
                    message = message.decode()
                    print('get ' + message)
                    time.sleep(1.0)
                    if message == 'exit':
                        break
                    message = None
            print('End program')
            sys.exit()


# クライアント側
import socket

print("client started")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    client.connect(('169.254.160.72', 50010))
    print('connected')

    while True:
        s = input()

        client.send(s.encode())
        
        if s == "exit":
            break

print("end.")