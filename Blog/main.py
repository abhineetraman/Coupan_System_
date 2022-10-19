from flask import render_template, Flask, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from os import remove
from flask_session import Session

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog_database.sqlite3'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = "filesystem"
Session(app)
db = SQLAlchemy()
db.init_app(app)
app.app_context().push()


class User(db.Model):
    __tablename__ = "User"
    sl_no = db.Column(db.Integer, autoincrement=True, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    uname = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)


class Blog(db.Model):
    __tablename__ = "Blog"
    sl_no = db.Column(db.Integer, autoincrement=True, primary_key=True)
    image = db.Column(db.LargeBinary, nullable=False)
    img_data = db.Column(db.String)
    uname = db.Column(db.String, db.ForeignKey("User.uname"), nullable=False)
    about = db.Column(db.String, nullable=False)


class Like_count(db.Model):
    __tablename__ = "Like_count"
    sl_no = db.Column(db.Integer, db.ForeignKey("Blog.sl_no"), primary_key=True)
    like = db.Column(db.Integer)


def user(string):
    usr = ''
    for c in string:
        if c != '@':
            usr += c
        else:
            break
    return usr


def password_checker(pd):
    flag = False
    if pd.isalnum() and pd.isdigit() is False and pd.isalpha() is False and len(pd) >= 8:
        flag = True
    return flag


@app.route("/", methods=["GET", "POST"])
def homepage():
    img = Blog.query.all()
    likes = Like_count.query.all()
    for i in range(len(img)//2):
        img[i], img[-i-1] = img[-i-1], img[i]
        likes[i], likes[-i-1] = likes[-i-1], likes[i]
    return render_template("homepage.html", img=img, likes=likes, error=None)


@app.route("/login", methods=["GET", "POST"])
def login():
    img = Blog.query.all()
    likes = Like_count.query.all()
    temp_log = User.query.all()
    error = "Email or password is incorrect"
    temp_email = request.form["email"]
    temp_pd = request.form["pd"]
    for i in temp_log:
        if i.email == temp_email and i.password == temp_pd:
            #session['user'] = user(i.email)
            return redirect("/home/"+temp_email)
    return render_template("homepage.html", img=img, likes=likes, error=error)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = 'Enter correct email'
    if request.method == "GET":
        return render_template("signup_page.html", error=None)
    if request.method == "POST":
        temp_email = request.form["email"]
        password = request.form["pd"]
        if '@' in temp_email and password_checker(password):
            login_id = User(email=temp_email, password=password, uname=user(temp_email))
            db.session.add(login_id)
            db.session.commit()
            return redirect("/")
        elif '@' in temp_email and password_checker(password) is False:
            return render_template("signup_page.html", error="Password should contains both alphabets and numbers")
        else:
            return render_template("signup_page.html", error=error)


@app.route("/home/<string:email>")
def home(email):
    #if not session.get('user'):
        #return redirect("/")
    img = Blog.query.filter_by(uname=user(email)).all()
    for i in img:
        imgd = i.image
        with open("static/img_file" + str(i.sl_no) + ".png", "wb") as bin_file:
            bin_file.write(imgd)
    usr = user(email)
    for i in range(len(img)//2):
        img[i], img[-i-1] = img[-i-1], img[i]
    return render_template("home.html", img=img, user=usr)


@app.route("/home/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        img = request.files["img"]
        data = img.read()
        tmp_email = request.form["email"]
        tmp_about = request.form["about"]

        tmp_usr = User.query.filter_by(email=tmp_email).one()
        if tmp_usr:
            tmp_blog = Blog(image=data, uname=user(tmp_email), img_data=img.filename, about=tmp_about)
            db.session.add(tmp_blog)
            db.session.commit()
            blog = Blog.query.all()
            sno = blog[-1].sl_no
            likes = Like_count(sl_no=sno, like=0)
            db.session.add(likes)
            db.session.commit()
            return redirect("/home/" + tmp_email)


@app.route("/home/<string:email>/delete/<int:sl_no>", methods=["GET"])
def delete(email, sl_no):
    temp_blog = Blog.query.filter_by(sl_no=sl_no, uname=user(email)).one()
    temp_like = Like_count.query.filter_by(sl_no=sl_no).one()
    if temp_like:
        db.session.delete(temp_like)
        db.session.commit()
    if temp_blog:
        remove("static/img_file" + str(sl_no) + ".png")
        db.session.delete(temp_blog)
        db.session.commit()
    return redirect("/home/" + email)


@app.route("/<int:sl_no>", methods=["GET"])
def like_btn(sl_no):
    likes = Like_count.query.filter_by(sl_no=sl_no).all()
    for i in likes:
        if i:
            count = i.like
            count += 1
            i.like = count
            db.session.commit()
        else:
            tmp_like = Like_count(sl_no=sl_no, like=1)
            db.session.add(tmp_like)
            db.session.commit()
    return redirect("/")


@app.route("/home/logout", methods=["GET"])
def logout():
    #session['user'] = None
    return redirect("/")


if __name__ == '__main__':
    app.debug = True
    app.run()
