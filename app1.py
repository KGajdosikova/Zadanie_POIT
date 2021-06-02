from threading import Lock
from flask import Flask, render_template, session, request, jsonify, url_for
from flask_socketio import SocketIO, emit, disconnect  
import time
import random
import math

import serial
import matplotlib.pyplot as plt
import numpy as np

ser=serial.Serial('/dev/ttyUSB0',9600)
ser.baudrate=9600
#ser.write(bytes('255','UTF-8'))

async_mode = None

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock() 


def background_thread(args):
    count = 0
    while True:
        A = dict(args).get('A')
        vysielaj = dict(args).get('vysielaj')
        print (A)
        print (args)
        print (vysielaj)
        socketio.sleep(0.5)
        count += 1
        read_ser=ser.readline()
        y=[]
        
        if vysielaj:
            y.append(float(read_ser))
            prem = y[-1]
            print(prem)
            count += 1
            prem = y    
            socketio.emit('my_response',
                          {'data': prem[-1], 'count': count},
                          namespace='/test')  

@app.route('/')
def main():
    return render_template('main.html', async_mode=socketio.async_mode)

@app.route('/index')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)
       
@app.route('/graphlive', methods=['GET', 'POST'])
def graphlive():
    return render_template('graphlive.html', async_mode=socketio.async_mode)

@app.route('/gauge', methods=['GET', 'POST'])
def gauge():
    return render_template('gauge.html', async_mode=socketio.async_mode)

@socketio.on('my_event', namespace='/test')
def test_message(message):   
    session['receive_count'] = session.get('receive_count', 0) + 1 
    session['A'] = message['value']    
    #emit('my_response',
        #{'data': message['value'], 'count': session['receive_count']})
 
@socketio.on('disconnect_request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()

@socketio.on('start_request', namespace='/test')
def start_request():
    session['vysielaj'] = 1
    print (session['vysielaj'])
    print (session)
         
@socketio.on('stop_request', namespace='/test')
def stop_request():
    session['vysielaj'] = 0
    print (session['vysielaj'])
    print (session)

@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread, args=session._get_current_object())
#    emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=80, debug=True)