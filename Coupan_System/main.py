from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from calendar import datetime
from random import randint


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///coupon_database.sqlite3'
db = SQLAlchemy()
db.init_app(app)
app.app_context().push()


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
    coupon_code = db.column(db.String, db.ForeignKey("coupon.coupon_code"))


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


class Coupon(db.Model):
    __tablename__ = "Coupon"
    sl_no = db.Column(db.Integer, primary_key=True)
    coupon_code = db.Column(db.String, primary_key=True)
    price = db.Column(db.String, nullable=False)
    validity = db.Column(db.String, nullable=False)
    issued_to = db.Column(db.String)



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
                return redirect("/" + role + "/" + fid)
        return render_template("login.html", error="Incorrect id or password")


@app.route("/student/<string:roll_no>/")
def home_student(roll_no):
    roll_no = str(roll_no)
    stu = studentInfo.query.filter_by(stu_id=roll_no).one()
    coup = Coupon.query.filter_by(issued_to=roll_no).all()
    return render_template("home_student.html", coup=coup, msg="", stu=stu)


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
def redeem(id,coupon_code):
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
        return render_template("add_stu.html",admin=admin)

    elif request.method == "POST":
        file = request.files["stu"]
        val = file.readlines()[1:]
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
    if request.method == "GET":
        return render_template("add_vendor.html", admin=admin)

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
        return redirect("/admin/" + admin_id)


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
        stu = studentInfo.query.filter_by(stu_id > low, stu_id < high).all()
        for i in stu:
            db.session.delete(i)
        db.session.commit()
        return redirect("/admin/" + admin_id)


@app.route("/<string:admin_id>/del_vendor")
def show_vendor(admin_id):
    vendor = vendorInfo.query.all()
    admin = AdminInfo.query.filter_by(admin_id=admin_id).one()
    return render_template("del_vendor.html", vendor=vendor, admin=admin)


@app.route("/<string:admin_id>/delete_vendor/<string:vendor_id>", methods=["POST", "GET"])
def delete_vendor(admin_id, vendor_id):
    vendor = vendorInfo.query.filter_by(vendor_id=vendor_id).one()
    db.session.delete(vendor)
    db.session.commit()
    vendor = Users.query.filter_by(id=vendor_id).one()
    db.session.delete(vendor)
    db.session.commit()
    return redirect("/admin/" + admin_id)


@app.route("/logout")
def logout():
    return redirect("/")


if __name__ == '__main__':
    app.debug = True
    app.run()
