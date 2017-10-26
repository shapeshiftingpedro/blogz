from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
import cgi
import jinja2

app = Flask(__name__)
app.config['DEBUG'] = True      # displays runtime errors in the browser, too
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:howmanyblogz@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(20))
    blogs = db.relationship("Postings" , backref="owner")
    
    def __init__(self, email, password):
        self.email = email
        self.password = password

    def __repr__(self):
        return '<User %r>' % self.email

class Postings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_title = db.Column(db.String(120))
    post_content = db.Column(db.String(255))
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __init__(self, post_title, post_content, owner):
        self.post_title = post_title
        self.post_content = post_content
        self.owner = owner

    def __rpr__(self):
        return "<Post %r>" % self.post_title

def get_post_list():
    return Postings.query.all()

def get_user_list():
    return User.query.all()

def get_user(nmbr):
    return User.query.filter_by(id=nmbr).first()

def get_user_post_list(user):
    return Postings.query.filter_by(owner_id=user).all()
 

@app.route("/register", methods=["POST","GET"])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        verify = request.form['pass_verif']
        if not is_email(email):
            flash('Whoops. "' + email + '" does not seem like an email address')
            return redirect('/register')
        email_db_count = User.query.filter_by(email=email).count()
        if email_db_count > 0:
            flash('Oh noes. "' + email + '" is already taken and password reminders are not implemented')
            return redirect('/register')
        if password != verify:
            flash('Passwords did not match')
            return redirect('/register')
        if len(password) <= 3:
            flash("Password is too short!")
            return redirect("/register")
        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        session["user"] = user.email
        return redirect("/newpost")
    else:
        return render_template("new-user.html")

@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users = User.query.filter_by(email=email)
        if users.count() == 1:
            user = users.first()
            if password == user.password:
                session["user"] = email
                flash('Hello again!, ' + user.email)
                return redirect("/")
        flash('Bad username or password, please try again')
        return redirect("/login")
    if request.method == 'GET':
        return render_template('user-login.html')


@app.route("/blog", methods=['GET'])
def posts_list():
    if request.args.get("id"):
        variable = int(request.args.get("id"))
        single_post = Postings.query.filter_by(id=variable).first()
        return render_template("post.html", post=single_post)
        
    
    elif request.args.get("user"):
        user_requested = int(request.args.get("user"))
        user_page = get_user_post_list(user_requested)
        return render_template("user.html", u_posts=user_page)
    
    elif request.args.get("user") == None and request.args.get("id") == None:
        posts = get_post_list()
        return render_template("posts.html", posts=posts)

@app.route("/newpost", methods=["GET"])
def load_new_post():
    return render_template("new-post.html")

@app.route("/newpost", methods=["POST"])
def new_post():
    new_title = request.form["title"]
    new_content = request.form["content"]
    new_owner = User.query.filter_by(email=session["user"]).first()
    
    if (not new_title) or (new_title.strip() == "") or (not new_content) or (new_content.strip() == ""): 
        flash("Please inlcude both a title and the post content")
        return render_template("new-post.html")


    post = Postings(post_title=new_title, post_content=new_content, owner=new_owner)
    db.session.add(post)
    db.session.commit()

    the_post = post.id

    return redirect("/blog?id=" + str(the_post))

def is_email(string):
    atsign_index = string.find('@')
    atsign_present = atsign_index >= 0
    if not atsign_present:
        return False
    elif len(string) <= 3:
        return False
    else:
        domain_dot_index = string.find('.', atsign_index)
        domain_dot_present = domain_dot_index >= 0
        return domain_dot_present


@app.route("/logout", methods=['POST'])
def logout():
    del session["user"]
    return redirect("/")

@app.route("/")
def index():
    user_list = get_user_list()
    return render_template('index.html', users = user_list)


endpoints_without_login = ["login", "register" , "index"]


@app.before_request
def require_login():
    if ("user" not in session and request.endpoint not in endpoints_without_login):
        return redirect("/login")

app.secret_key = 'p&Zr@8I/3ye w~E*H!j+N(L!X1-?zS'

if __name__ == "__main__":
    app.run()