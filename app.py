import hashlib
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)
cors = CORS(app, resources={r'*': {'origins': '*'}})
client = MongoClient('localhost', 27017)
db = client.turtlegram

@app.route("/")
def hello_word():
    return jsonify({'msg':'success'})

@app.route("/signup", methods=["POST"])
def sign_up():
    
    data = json.loads(request.data)
    
    password_hash = hashlib.sha256(data['password'].encode('utf-8')).hexdigest()
    
    doc = {
        'email' : data.get('email'),
        'password' : password_hash
    }
    
    db.users.insert_one(doc)
    
    return jsonify({'msg':'success'})



if __name__ =='__main__':
    app.run('0.0.0.0', port=5000, debug=True)