
from flask_cors import CORS, cross_origin
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
import pickle
from flask import Flask, flash, render_template, redirect, session, request, url_for, Response
from flask_restful import Api, Resource, reqparse
import pytesseract
import cv2
from PIL import Image
import os
import werkzeug
from math import floor
import base64
import urllib.request
from flask_mysqldb import MySQL, MySQLdb
import bcrypt
from werkzeug.utils import secure_filename
pytesseract.pytesseract.tesseract_cmd = r'D:\INSTALLED\TESSERACT\tesseract.exe'
REDUCTION_COEFF = 0.9
QUALITY = 85
app = Flask(__name__)
api = Api(app)
parser = reqparse.RequestParser()
parser.add_argument(
    'file', type=werkzeug.datastructures.FileStorage, location='files')
cors = CORS(app)
app.secret_key = "secret key"
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flaskdb'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/about/')
def about():
    return render_template('about.html')


@app.route('/upload/', methods=['GET', 'POST'])
def upload():
    if 'loggedin' in session:
        try:
            imagefile = request.files.get('imagefile', '')
            file = request.files['imagefile'].read()
            img = Image.open(imagefile)
            img1 = img.convert('LA')
            print("Before reducing", img1.size)
            imgsize = len(file) >> 20
            if imgsize > 2:
                x, y = img1.size
                x *= REDUCTION_COEFF
                y *= REDUCTION_COEFF
                img1 = img1.resize((floor(x), floor(y)), Image.BICUBIC)
                print("Img reduced", img1.size)
            ext = "jpeg"
            if "." in imagefile.filename:
                ext = imagefile.filename.rsplit(".", 1)[1]
            text = pytesseract.image_to_string(img1)
            img_base64 = base64.b64encode(file)
            img_base64_str = str(img_base64)
            img_base64_str = "data:image/" + ext + ";base64," + \
                img_base64_str.split('\'', 1)[1][0:-1]
            f = open("sample.txt", "a")
            f.truncate(0)
            f.write(text)
            f.close()
            return render_template('result.html',var=text, img=img_base64_str)

        except Exception as e:
            print(e)
            return render_template('error.html')
    return redirect(url_for('login'))


@app.route("/gettext")
def gettext():
    with open("sample.txt") as fp:
        src = fp.read()
    return Response(src, mimetype="text/csv", headers={"Content-disposition": "attachment; filename=sample.txt"})


@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    model = pickle.load(open('log_reg.pkl', 'rb'))
    train_df = pd.read_csv("train.csv")
    train_df.drop('id', axis=1, inplace=True)
    vec_tfid = TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_df=0.9, strip_accents='unicode',
                               use_idf=1, smooth_idf=1, sublinear_tf=1, max_features=40000)
    target = ['toxic', 'severe_toxic', 'obscene',
              'threat', 'insult', 'identity_hate']
    for i, label in enumerate(target):
        X = train_df.comment_text
        y = train_df[label]
    x_dtm = vec_tfid.fit_transform(X)
    pred_prob1 = []
    if request.method == 'POST':
        text = request.form['inputforcomment']
    comment_vec = vec_tfid.transform([text])
    count = 0
    result = ""
    for i in range(len(target)):
        y = train_df[target[i]]
        model.fit(x_dtm, y)
        pred_prob = model.predict_proba(comment_vec)[:, 1][0]
        pred_prob1.append(pred_prob)
        if (pred_prob > 0.4):
            print(target[i], pred_prob*100, '%')
            result += target[i]
            result += '   '
            print(type(result))
            count = count+1
    if (count == 0):
        result += 'non toxic'
        print("Non toxic")
    return render_template('prediction.html', predict=result)


class UploadAPI(Resource):
    def get(self):
        print("check passed")
        return {"message": "API For TextExtractor2.0"}, 200

    def post(self):
        data = parser.parse_args()
        if data['file'] == "":
            return {'message': 'No file found'}, 400

        photo = data['file']
        if photo:
            photo.save(os.path.join("./static/images/", photo.filename))
            img = Image.open(photo)
            img1 = img.convert("LA")
            text = pytesseract.image_to_string(img1)
            print("check 1 passed")
            os.remove(os.path.join("./static/images/", photo.filename))
            return {"message": text}, 200
        else:
            return {'message': 'Something went wrong'}, 500


api.add_resource(UploadAPI, "/api/v1/")


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    else:
        name = request.form['name']
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        hash_password = bcrypt.hashpw(password, bcrypt.gensalt())
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (name, email, password) VALUES (%s,%s,%s)",
                    (name, email, hash_password,))
        mysql.connection.commit()
        session['name'] = request.form['name']
        session['email'] = request.form['email']
        session['loggedin'] = True
        return redirect(url_for('home'))


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        curl = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        curl.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = curl.fetchone()
        curl.close()
        if len(user) > 0:
            if bcrypt.hashpw(password, user["password"].encode('utf-8')) == user["password"].encode('utf-8'):
                session['name'] = user['name']
                session['email'] = user['email']
                session['loggedin'] = True
                return render_template("index.html")
            else:
                return "Error password and email not match"
        else:
            return "Error user not found"
    else:
        return render_template("login.html")


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.clear()
    return render_template("index.html")


if __name__ == "__main__":
    app.run()
