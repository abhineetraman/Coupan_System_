from flask import Flask, render_template, request, redirect, session
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from calendar import datetime
from os.path import join


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///coupon_database.sqlite3'
app.config['UPLOAD_FOLDER'] = 'static'
app.config['MAX_CONTENT_PATH'] = '1000000'
app.secret_key = 'asking_is_not_good'
db = SQLAlchemy()
api = Api(app)
db.init_app(app)
app.app_context().push()

timestamp, cost, receiving_vendor = " ", 0, " "


class Users(db.Model):
    __tablename__ = "Users"
    id = db.Column(db.String, primary_key=True)
    password = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False)


class studentInfo(db.Model):
    __tablename__ = "studentInfo"
    stu_id = db.Column(db.String, db.ForeignKey("Users.id"), primary_key=True)
    name = db.Column(db.String, nullable=False)
    dept = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)


class vendorInfo(db.Model):
    __tablename__ = "vendorInfo"
    vendor_id = db.Column(db.String, db.ForeignKey("Users.id"), primary_key=True)
    vendor_name = db.Column(db.String, nullable=False)
    issued_dept = db.Column(db.String)


class AdminInfo(db.Model):
    __tablename__ = "admin"
    admin_id = db.Column(db.String, db.ForeignKey("Users.id"), primary_key=True)
    name = db.Column(db.String, nullable=False)
    dept = db.Column(db.String, nullable=False)


class events(db.Model):
    __tablename__ = "events"
    sl_no = db.Column(db.Integer, autoincrement=True, primary_key=True)
    timestamp = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    issue_dept = db.Column(db.String, nullable=False)
    spokesperson = db.Column(db.String, nullable=False)
    mode = db.Column(db.String, nullable=False)
    created_by = db.Column(db.String, db.ForeignKey("admin.admin_id"), nullable=False)


class Coupon(db.Model):
    __tablename__ = "Coupon"
    sl_no = db.Column(db.Integer, primary_key=True)
    coupon_code = db.Column(db.String, primary_key=True)
    price = db.Column(db.String, nullable=False)
    validity = db.Column(db.String, nullable=False)
    issued_to = db.Column(db.String)


class Registration(db.Model):
    __tablename__ = "registration"
    sl_no = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.String, nullable=False)
    roll_no = db.Column(db.String, db.ForeignKey("studentInfo.stu_id"), nullable=False)
    dept = db.Column(db.String, nullable=False)
    email = db.Column(db.String, db.ForeignKey("studentInfo.email"), nullable=False)
    registered_event = db.Column(db.String, db.ForeignKey("events.name"), nullable=False)
    attended = db.Column(db.String)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", error=None)
    elif request.method == "POST":
        fid = request.form["fid"]
        fpassword = request.form["fpassword"]
        user = Users.query.all()
        for i in user:
            if fid == i.id and fpassword == i.password:
                role = i.role
                session['username'] = fid
                return redirect("/" + role + "/" + fid)
        return render_template("login.html", error="Incorrect id or password")


@app.route("/student/<string:roll_no>")
def home_student(roll_no):
    roll_no = str(roll_no)
    stu = studentInfo.query.filter_by(stu_id=roll_no).one()
    coup = Coupon.query.filter_by(issued_to=roll_no).all()
    return render_template("home_student.html", coup=coup, msg="", stu=stu)


@app.route("/event_admin/<string:id>")
def home_event_admin(id):
    admin = AdminInfo.query.filter_by(admin_id=id).one()
    event = events.query.filter_by(created_by=id).all()
    total = len(event)
    for i in range(total//2):
        event[i], event[-i] = event[-i], event[i]
    return render_template("event_admin_home.html", admin=admin, event=event)


@app.route("/vendor/<string:vendor_id>")
def home_vendor(vendor_id):
    vendor = vendorInfo.query.filter_by(vendor_id=vendor_id).one()
    coup = Coupon.query.filter_by(issued_to=vendor_id).all()
    return render_template("home_vendor.html", coup=coup, vendor=vendor)


@app.route("/admin/<string:admin_id>")
def home_admin(admin_id):
    coup = Coupon.query.filter_by(issued_to=admin_id).all()
    admin = AdminInfo.query.filter_by(admin_id=admin_id).one()
    return render_template("home_admin.html", coup=coup, admin=admin)


@app.route("/<string:admin_id>/generate", methods=["GET", "POST"])
def generate_coupon(admin_id):
    admin = AdminInfo.query.filter_by(admin_id=admin_id).one()
    vendor = vendorInfo.query.all()
    if request.method == "GET":
        return render_template("generation_coupon.html", admin_id=admin_id, vend=vendor)
    elif request.method == "POST":
        price = request.form["price"]
        validity = request.form["validity"]
        issued_vendor = request.form.__getitem__("vname")
        vendor = vendorInfo.query.filter_by(vendor_id=issued_vendor).one()
        dept, year, C_code, id = " ", " ", " ", " "
        if admin:
            dept = admin.dept
            year = str(datetime.date.today())[2:4:]
            id = admin.admin_id
        stu = studentInfo.query.filter_by(dept=dept).all()
        quantity = len(stu)
        for i in range(1, quantity+1):
            if len(str(i)) == 1:
                C_code = dept + year + "00" + str(quantity)
            elif len(str(i)) == 2:
                C_code = dept + year + "0" + str(quantity)
            elif len(str(i)) == 3:
                C_code = dept + year + str(quantity)
            tmp_Coupon = Coupon(sl_no=quantity, coupon_code=C_code, price=price, validity=validity, issued_to=id)
            db.session.add(tmp_Coupon)
        vendor.issued_dept = dept
        db.session.commit()
        return redirect("/" + admin_id + "/transfer")


@app.route("/<string:admin_id>/transfer")
def transfer(admin_id):
    ad = AdminInfo.query.filter_by(admin_id=admin_id).one()
    if ad:
        dept = ad.dept
        tmp_stu = studentInfo.query.filter_by(dept=dept).all()
        tmp_coup = Coupon.query.filter_by(issued_to=admin_id).all()
        for i in range(len(tmp_stu)):
            tmp_stu[i].coupon_code = tmp_coup[i].coupon_code
            tmp_coup[i].issued_to = tmp_stu[i].stu_id
        db.session.commit()
        return redirect("/admin" + admin_id)

    return redirect("/admin/" + admin_id)


@app.route("/<string:id>/redeem/<string:coupon_code>")
def redeem(id, coupon_code):
    coup = Coupon.query.filter_by(coupon_code=coupon_code).one()
    if coup:
        dept = coup.coupon_code[0:2:]
        vendor = vendorInfo.query.filter_by(issued_dept=dept).all()
        ven = None
        for i in vendor:
            print(i)
            if i.issued_dept == str(coup.coupon_code)[0:2:]:
                ven = i
                print(ven, i)
        coup.issued_to = ven.vendor_id
        db.session.commit()
        return redirect("/student/" + id)
    else:
        return redirect("/student/" + id)


@app.route("/<string:admin_id>/add_stu", methods=["POST", "GET"])
def add_stu(admin_id):
    admin = AdminInfo.query.filter_by(admin_id=admin_id).one()
    dept = " "
    if admin:
        dept = admin.dept

    if request.method == "GET":
        return render_template("add_stu.html", admin=admin)

    elif request.method == "POST":
        file = request.files["stu"]
        file.save(join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename)))
        f = open("static/" + secure_filename(file.filename), 'r')
        val = f.readlines()[1:]
        for i in val:
            fields = i.split(',')
            roll_no = fields[0]
            name = fields[1]
            dob = fields[2]
            user = Users(id=roll_no, password=dob, role='Student')
            stu = studentInfo(stu_id=roll_no, name=name, dept=dept)
            db.session.add(user)
            db.session.commit()
            db.session.add(stu)
            db.session.commit()
        return redirect("/admin/" + admin_id)


@app.route("/<string:admin_id>/add_vendor", methods=["GET", "POST"])
def add_vendor(admin_id):
    admin = AdminInfo.query.filter_by(admin_id=admin_id).one()
    user = Users.query.filter_by(id=admin_id).one()
    if request.method == "GET":
        return render_template("add_vendor.html", admin=admin, user=user)

    elif request.method == "POST":
        name = request.form["vname"]
        dob = str(request.form["dob"])
        vid = name[:4:] + dob[:4:]
        v_user = Users(id=vid, password=dob, role="vendor")
        db.session.add(v_user)
        db.session.commit()
        tmp_vendor = vendorInfo(vendor_id=vid, vendor_name=name)
        db.session.add(tmp_vendor)
        db.session.commit()
        if user:
            return redirect("/" + user.role + "/" + admin_id)


@app.route("/<string:admin_id>/del_stu", methods=["POST", "GET"])
def delete_stu(admin_id):
    admin = AdminInfo.query.filter_by(admin_id=admin_id).one()
    dept = " "
    if admin:
        dept = admin.dept
    if request.method == "GET":
        stu = studentInfo.query.filter_by(dept=dept).all()
        return render_template("del_student.html", stu=stu, admin=admin)
    elif request.method == "POST":
        low = request.form["low"]
        high = request.form["high"]
        stu = db.session.query(studentInfo).filter(studentInfo.stu_id > str(low)).all()
        for i in stu:
            if i.stu_id < str(high):
                tmp_user = Users.query.filter_by(id=i.stu_id).one()
                db.session.delete(i)
                db.session.delete(tmp_user)
        db.session.commit()
        return redirect("/admin/" + admin_id)


@app.route("/<string:admin_id>/del_vendor")
def show_vendor(admin_id):
    vendor = vendorInfo.query.all()
    admin = AdminInfo.query.filter_by(admin_id=admin_id).one()
    user = Users.query.filter_by(id=admin_id).one()
    return render_template("del_vendor.html", vendor=vendor, admin=admin, user=user)


@app.route("/<string:admin_id>/delete_vendor/<string:vendor_id>", methods=["POST", "GET"])
def delete_vendor(admin_id, vendor_id):
    vendor = vendorInfo.query.filter_by(vendor_id=vendor_id).one()
    db.session.delete(vendor)
    db.session.commit()
    vendor = Users.query.filter_by(id=vendor_id).one()
    db.session.delete(vendor)
    db.session.commit()
    user = Users.query.filter_by(id=admin_id).one()
    if user:
        return redirect("/" + user.role + "/" + admin_id)


@app.route("/<string:admin_id>/attendance/<int:event_id>", methods=["GET", "POST"])
def attendance(admin_id, event_id):
    admin = AdminInfo.query.filter_by(admin_id=admin_id).one()
    event = events.query.filter_by(sl_id=event_id).one()
    event_name = " "
    if event:
        event_name = event.name
    registered_candidate = Registration.query.filter_by(regisrted_event=event_name).all()
    if request.method == "GET":
        return render_template("attendance.html", admin=admin, candidate=registered_candidate, event_name=event_name, event_id=event_id)
    elif request.method == "POST":
        for i in registered_candidate:
            value = request.form.getlist(i.sl_no)
            if value:
                i.atteded = "Yes"
                id, password, dept, name = i.id, i.email, i.dept, i.name
                user = Users.query.filter_by(id=id).one()
                if not user:
                    tmp_user = Users(id=id,password=password,role=student)
                    tmp_stu = studentInfo(stu_id=id, name=name, dept=dept, email=email)
        db.session.commit()
        participants = Registration.query.filter_by(registered_event=event_name).all()
        quantity = len(participants)
        year = str(datetime.date.today())[2:4:]
        for i in range(1, quantity + 1):
            if len(str(i)) == 1:
                C_code = event_name[0:3:].toupper() + year + "00" + str(quantity)
            elif len(str(i)) == 2:
                C_code = event_name[0:3:].toupper() + year + "0" + str(quantity)
            elif len(str(i)) == 3:
                C_code = event_name[0:3:].toupper() + year + str(quantity)
            tmp_Coupon = Coupon(sl_no=quantity, coupon_code=C_code, price=price, validity=timestamp, issued_to=participants[i].roll_no)
            db.session.add(tmp_Coupon)
        vendor.issued_dept = event_name
        db.session.commit()
        return redirect("/event_admin" + admin_id)


@app.route("/<string:admin_id>/add_event", methods=["GET", "POST"])
def add_event(admin_id):
    admin = AdminInfo.query.filter_by(admin_id=admin_id).one()
    vend = vendorInfo.query.all()
    dept = ""
    if admin:
        dept = admin.dept
    if request.method == "GET":
        return render_template("add_event.html", admin=admin, vend=vend)
    elif request.method == "POST":
        file =request.files["register"]
        event_name = request.form["ename"]
        spokesperson = request.form["sname"]
        mode = request.form["mode"]
        timestamp = request.form["timestamp"]
        price = request.form["price"]
        receiving_vendor = request.form.__getitem__("vname")
        event = events(timestamp=timestamp, name=event_name, spokesperson=spokesperson, mode=mode, issue_dept=dept, created_by=admin_id)

        db.session.add(event)
        db.session.commit()

        file.save(join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename)))
        f = open("static/" + secure_filename(file.filename), 'r')
        val = f.readlines()[1:]
        for i in val:
            fields = i.split(',')
            roll_no = fields[0]
            name = fields[1]
            dept = fields[2]
            email = fields[3]
            register = Registration(name=name, roll_no=roll_no, dept=dept, email=email, registered_event=event_name)
            db.session.add(register)
        db.session.commit()
        return redirect("/event_admin/" + admin_id)


@app.route("/<string:admin_id>/del_event/<int:sl_no>")
def del_event(admin_id, sl_no):
    event = events.query.filter_by(sl_no=sl_no).one()
    if event:
        db.session.delete(event)
        db.session.commit()
        return redirect("/event_admin" + admin_id)


@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect("/")


from Api.api import AdminAPI, StudentAPI
#api.add_resourse(AdminAPI, "/api/admin/<string:admin_id>", "/api/event_admin/<string:id>", "/api/vendor/<string:vendor_id>")
#api.add_resourse(StudentAPI, "/api/student/<string:roll_no>")


if __name__ == '__main__':
    app.debug = True
    app.run(host="0.0.0.0", port="8080")
