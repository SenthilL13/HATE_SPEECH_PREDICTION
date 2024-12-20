from flask_cors import CORS
import numpy as np
from flask import Flask, flash, render_template, redirect, session, request, url_for, Response
from flask_restful import Api, Resource, reqparse
import pytesseract
import cv2
from PIL import Image
import os
import werkzeug
from math import floor
import base64
import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from flask_mysqldb import MySQL
import bcrypt
from werkzeug.utils import secure_filename

# Configuration for Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Flask app setup
app = Flask(__name__)
api = Api(app)
cors = CORS(app)

# App secret key and database configuration
app.secret_key = "secret_key"
app.config['MYSQL_HOST'] = 'bkce8c6kcgjidjd2iq61-mysql.services.clever-cloud.com'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'uydpmttetns1g8yn'
app.config['MYSQL_PASSWORD'] = '9k9ij3JyUXJu2sBdEC9z'
app.config['MYSQL_DB'] = 'bkce8c6kcgjidjd2iq61'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['MYSQL_POOL_SIZE'] = 5
app.config['MYSQL_POOL_TIMEOUT'] = 30

mysql = MySQL(app)
parser = reqparse.RequestParser()
parser.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files')

REDUCTION_COEFF = 0.9
QUALITY = 85

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about/')
def about():
    return render_template('about.html', message="This is the About Page!")

@app.route('/upload/', methods=['GET', 'POST'])
def upload():
    if 'loggedin' in session:
        try:
            imagefile = request.files.get('imagefile', '')
            file = imagefile.read()
            img = Image.open(imagefile)
            img1 = img.convert('LA')

            # Reduce image size if greater than 2 MB
            if len(file) > (2 << 20):
                x, y = img1.size
                x *= REDUCTION_COEFF
                y *= REDUCTION_COEFF
                img1 = img1.resize((floor(x), floor(y)), Image.BICUBIC)

            ext = "jpeg"
            if "." in imagefile.filename:
                ext = imagefile.filename.rsplit(".", 1)[1]

            text = pytesseract.image_to_string(img1)
            img_base64 = base64.b64encode(file).decode('utf-8')
            img_base64_str = f"data:image/{ext};base64,{img_base64}"

            with open("sample.txt", "w") as f:
                f.write(text)

            return render_template('result.html', var=text, img=img_base64_str)

        except Exception as e:
            print(f"Error: {e}")
            return render_template('error.html')
    return redirect(url_for('login'))

@app.route("/gettext")
def gettext():
    with open("sample.txt") as fp:
        src = fp.read()
    return Response(src, mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=sample.txt"})

@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    try:
        model = pickle.load(open('log_reg.pkl', 'rb'))
        train_df = pd.read_csv("train.csv")
        train_df.drop('id', axis=1, inplace=True)

        vec_tfid = TfidfVectorizer(lowercase=True, stop_words=None)
        X = train_df['comment_text']
        x_dtm = vec_tfid.fit_transform(X)

        if request.method == 'POST':
            text = request.form['inputforcomment']
            comment_vec = vec_tfid.transform([text])
            result = ""

            for label in ['toxic', 'severe_toxic', 'obscene', 'threat', 'insult', 'identity_hate']:
                y = train_df[label]
                model.fit(x_dtm, y)
                pred_prob = model.predict_proba(comment_vec)[:, 1][0]
                if pred_prob > 0.4:
                    result += f"{label}: {pred_prob*100:.2f}%\n"

            if not result:
                result = "Non-toxic"

            return render_template('prediction.html', predict=result)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('error.html')

class UploadAPI(Resource):
    def get(self):
        return {"message": "API For TextExtractor2.0"}, 200

    def post(self):
        data = parser.parse_args()
        if not data['file']:
            return {'message': 'No file found'}, 400

        photo = data['file']
        try:
            photo.save(os.path.join("./static/images/", photo.filename))
            img = Image.open(photo)
            img1 = img.convert("LA")
            text = pytesseract.image_to_string(img1)
            os.remove(os.path.join("./static/images/", photo.filename))
            return {"message": text}, 200
        except Exception as e:
            print(f"Error: {e}")
            return {'message': 'Something went wrong'}, 500

api.add_resource(UploadAPI, "/api/v1/")

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        try:
            name = request.form['name']
            email = request.form['email']
            password = request.form['password'].encode('utf-8')
            hash_password = bcrypt.hashpw(password, bcrypt.gensalt())

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                        (name, email, hash_password,))
            mysql.connection.commit()
            session['name'] = name
            session['email'] = email
            session['loggedin'] = True

            return redirect(url_for('home'))
        except Exception as e:
            print(f"Error: {e}")
            return render_template('error.html')
    return render_template("register.html")

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')

        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cur.fetchone()

            if user and bcrypt.checkpw(password, user['password'].encode('utf-8')):
                session['name'] = user['name']
                session['email'] = user['email']
                session['loggedin'] = True
                return redirect(url_for('home'))
            else:
                flash("Incorrect email or password.")
        except Exception as e:
            print(f"Error: {e}")
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
