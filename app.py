from flask import Flask, request, render_template, send_file, request, Response
import json
import boto3
import cv2
import datetime, time
import os, sys
import numpy as np
from threading import Thread

global capture
capture=0

account_id = ""
account_key = ""
account_token = ""

if os.path.exists('./shots') == False:
    os.mkdir('./shots')

app = Flask(__name__, template_folder='./templates')

camera = cv2.VideoCapture(0)

def client():
    global account_id
    global account_key
    global account_token
    print(account_id, account_key, account_token)
    client = boto3.client("textract", aws_access_key_id=account_id,
                          aws_secret_access_key=account_key,
                          aws_session_token=account_token,
                          region_name='us-east-1')
    return client

def gen_frames():
    global capture
    while True:
        success, frame = camera.read() 
        if success:  
            if(capture):
                capture=0
                now = datetime.datetime.now()
                p = os.path.sep.join(['shots', "shot.png".format(str(now).replace(":",''))])
                cv2.imwrite(p, frame)       
            try:
                ret, buffer = cv2.imencode('.jpg', cv2.flip(frame,1))
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                pass
                
        else:
            pass

app = Flask(__name__)

@ app.route("/", methods=["GET"])
def main():
    extractedText = ""
    responseJson = {

        "text": extractedText
    }
    return render_template("login.html", jsonData=json.dumps(responseJson))


@ app.route("/login", methods=["POST"])
def login():
    global account_id
    global account_key
    global account_token
    global textractclient
    account_id = request.form.get("aws_id")
    account_key = request.form.get("aws_key")
    account_token = request.form.get("aws_token")
    return render_template("home.html", jsonData=json.dumps({}))


@ app.route("/extracttext", methods=["POST"])
def extractImage():
    file = request.files.get("filename")
    binaryFile = file.read()
    textractclient = client()
    response = textractclient.detect_document_text(
        Document={
            'Bytes': binaryFile
        }
    )
    extractedText = ""
    for block in response['Blocks']:
        if block["BlockType"] == "LINE":
            extractedText = extractedText+block["Text"]+" "

    responseJson = {

        "text": extractedText
    }
    print("This is response file: ")
    print(response)
    print("This is result file:")
    print(responseJson)
    return render_template("home.html", jsonData=json.dumps(responseJson))

@app.route('/camera', methods=["POST"])
def index():
    return render_template('camera.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/requests',methods=['POST','GET'])
def tasks():
    global switch,camera
    if request.method == 'POST':
        if request.form.get('click') == 'Capture':
            global capture
            capture=1     
    elif request.method=='GET':
        return render_template('camera.html')
    return render_template('camera.html')

@app.route('/download')
def download_file():
    return


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)

camera.release()
