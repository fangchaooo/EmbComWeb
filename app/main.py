import time
from threading import Thread, Lock
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room,close_room, rooms, disconnect
import sys
import glob
import serial
import json
import struct


# define Flask-SocketiIO and Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


serialConnected = False
serialPort = 0
serialLock = Lock()


# serial port-----------------------------------------------------
# serial platform find and all serial in this platform
def serial_ports():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in list(range(256))]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')
    result = []
    for port in ports:
        try:
            print("checking port "+port)
            s = serial.Serial(port)
            print("closing port "+port)
            s.close()
            result.append(port)
        except(serial.SerialException):
            pass
    return result


# send serial port to html with json string
@socketio.on('connect')
def test_connect():
    print('hey someone connected')
    # generate list of currently connected serial ports
    ports = serial_ports()
    print(ports)
    new_b=[]
    for p in ports:
        new_b.append({"comName": p})
    print(json.dumps(new_b))
    # emit socket with serial ports in it
    emit('serial list display', new_b)


# the string of serial port select send to service
@socketio.on('serial select')
def action(port):
    global serial_selection
    print('serial port changed to %s' %(port))
    serial_selection = port
# serial port-----------------------------------------------------

# baud select----------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

    
@socketio.on('baud select')
def action(baud):
    global baud_selection
    print('baud changed to %s' %(baud))
    baud_selection = baud


if __name__ == "__main__": 
    socketio.run(app, port=3000, debug=True)
 
