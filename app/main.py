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
thread = None
serialConnected = False
serialPort = 0
serialLock = Lock()


# main threading
def serial_thread():
    print("Starting serial background thread.")
    while True:
        if serialConnected:
            print("serial connected!")
            time.sleep(2)
            serialLock.acquire()
            try:
                new_setup_string = serialPort.read()
                serialPort.flushInput()
            except :
                print("initi string reading issue")
            serialLock.release()
            while serialConnected:
                serialLock.acquire()
                s = serialPort.read()
                try:
                    add_data(s)
                    socketio.emit('add_text', s, broadcast =True)
                except:
                    print("failed socket")
                serialLock.release()


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
            print("serial error")
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
@socketio.on('baud select')
def action(baud):
    global baud_selection
    print('baud changed to %s' %(baud))
    baud_selection = baud

# connect serial
@socketio.on('serial connect request')
def connection(already_built):
    global serialConnected
    global serialPort
    global serialLock
    global alternate
    global isSetup
    isSetup = already_built['state'] #user this
    print(isSetup)
    print ('Trying to connect to: ' + serial_selection + ' ' + str(baud_selection))
    print (serialLock)
    print (serialConnected)
    try:
        serialLock.acquire()
        print ("Lock acquired")
        serialPort = serial.Serial(serial_selection, int(baud_selection),timeout=4)
        print ('SerialPort')
        print ('Connected to ' + str(serial_selection) + ' at ' + str(baud_selection) + ' BAUD.')
        emit('serial connected', broadcast=True) #tells page to indicate connection (in button)
        serialPort.flushInput()
        #serialPort.flushOutput()
        serialLock.release()
        serialConnected = True #set global flag
    except:
        print ("Failed to connect with "+str(serial_selection) + ' at ' + str(baud_selection) + ' BAUD.')


@socketio.on('serial disconnect request')
def dis_con():
    global serialConnected
    global serialLock
    global serialPort
    print ('Trying to disconnect...')
    serialLock.acquire()
    serialPort.close()
    serialLock.release()
    serialConnected = False
    emit('serial disconnected',broadcast=True)
    print ('Disconnected...good riddance' )


@socketio.on("disconnected")
def ending_it():
    print ("We're done")


@socketio.on('add_text')
def add_data(data):
    if data == '':
        emit('append data', 1)
    emit('append data', data)



@app.route('/')
def index():
    global thread
    print("A user connected")
    if thread is None:
        thread = Thread(target=serial_thread)
        thread.daemon = True
        thread.start()
    return render_template('index.html')




if __name__ == "__main__": 
    socketio.run(app, port=3000, debug=True)
 
