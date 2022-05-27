from functools import wraps
import hashlib
import json
from re import S
from bson import ObjectId
import jwt
from datetime import datetime, timedelta
from flask import Flask, abort, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient

SECRET_KEY = 'turtle'

app = Flask(__name__)
cors = CORS(app, resources={r'*': {'origins': '*'}})
client = MongoClient('localhost', 27017)
db = client.turtlegram


#데코레이터 함수 로그인한 유저정보(토큰)을 불러오는 역할
def authorize(f):
    @wraps(f) 
    def decorated_function(*args, **kwargs):     #*args 는 리스트형태로 인자가 얼마든지 들어와도된다 #**kwargs는 keyword 머머는 머 형태로 얼마든지 들어와도 인식을하겠다.
        if not 'Authorization' in request.headers:
            abort(401)
        token = request.headers['Authorization']
        try:
            user = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except: 
            abort(401)
        return f(user, *args, **kwargs)        
        
    return decorated_function



@app.route("/")
@authorize
def hello_word(user):
    print(user)
    return jsonify({'msg':'success'})

#회원가입
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

#로그인
@app.route("/login", methods=["POST"])
def login():
    data = json.loads(request.data)
    
    email = data.get("email")
    password = data.get("password")
    
     # 회원가입 때와 같은 방법으로 pw를 암호화합니다.
    hashed_pw = hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    result = db.users.find_one({
        'email': email, 
        'password': hashed_pw
    })
    
    if result:
       
        
        payload = {
            'id': str(result["_id"]),
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)
        }
        token = jwt.encode(payload=payload, key=SECRET_KEY, algorithm='HS256')
        
    
        return jsonify({'result': 'success', 'token': token})
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})
    
    
#유저 정보 불러오기
@app.route("/getuserinfo", methods=["GET"])
@authorize
def get_user_info(user):
    result = db.users.find_one({
        '_id': ObjectId(user["id"])
    })
    
    print(result)
    
    
    
    return jsonify({"msg": "success", "email": result["email"]})

#게시글 쓰기
@app.route("/article", methods=["POST"])
@authorize
def post_article(user):
    data = json.loads(request.data)
    print(data)
    
    db_user = db.users.find_one({'_id': ObjectId(user.get('id'))})
    now = datetime.now().strftime("%H:%M:%S")
    doc = {
        'title' : data.get('title', None),
        'content' : data.get('content', None),
        'user' : user['id'],
        'user_email' : db_user['email'],
        'time' : now
    }
    print(doc)
    
    db.article.insert_one(doc)
    
    
    
    return jsonify({"msg":"success"})

#게시글 불러오기
@app.route("/article", methods=["GET"])
def get_article():
    articles = list(db.article.find())
    for article in articles:
        article["_id"] = str(article["_id"])

    return jsonify({"msg":"success", "articles": articles})

#게시글 상세페이지
@app.route("/article/<article_id>", methods=["GET"])
def get_article_detail(article_id):
    print(article_id)
    article = db.article.find_one({"_id": ObjectId(article_id)})
    print(article)
    article["_id"] = str(article["_id"])
    
    return jsonify({"msg":"success", "article": article})

# 게시글 수정
@app.route("/article/<article_id>", methods=["PATCH"])
@authorize
def patch_article_detail(user, article_id):
    
    data = json.loads(request.data)
    title = data.get('title')
    content = data.get('content')
    
    article = db.article.update_one({'_id': ObjectId(article_id), "user": user["id"]}, {
        "$set": {"title": title, "content": content}})
    print(article.matched_count)
    
    if article.matched_count:
        return jsonify({"msg": "success"})
    
    return jsonify({"msg": "fail"}), 403

#게시글 삭제
@app.route("/article/<article_id>", methods=["DELETE"])
@authorize
def delete_article_detail(user, article_id):

    article = db.article.delete_one(
        {"_id": ObjectId(article_id), "user": user["id"]})

    if article.deleted_count:
        return jsonify({"message": "success"})
    else:
        return jsonify({"message": "fail"}), 403
    

if __name__ =='__main__':
    app.run('0.0.0.0', port=5000, debug=True)