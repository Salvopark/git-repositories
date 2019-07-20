# all the imports
import sqlite3, urllib, json, os
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from passlib.hash import pbkdf2_sha256
import git_parser
import gc

application = Flask(__name__)
app = application
# this will read in variables from config.py
app.config.from_object("config")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)


# ====================================================================================
# setup and teardown for each HTTP request
# ====================================================================================
# the @ sign here means that app.before_request is a "decorator" for the function
# defined in the next line. http://legacy.python.org/dev/peps/pep-0318/#current-syntax
# but you don't have to understand that to use it
#
# in a flask app, putting @app.before_request before a function means
# that this function will be called before a request is routed, and app.teardown_request
# is called after everything is finished.
# So this is a good place to connect/disconnect to the database

@app.before_request
def before_request():
    g.dir = os.path.dirname(os.path.abspath(__file__))
    g.db = sqlite3.connect(g.dir + '/' + app.config['DATABASE'])


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

# ==============================================================================
# Database declarations
# ==============================================================================


class User(db.Model):
    email = db.Column(db.String(50), unique=True, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Post(db.Model):
    title = db.Column(db.String(50), nullable=False, primary_key=True)
    description = db.Column(db.Text)
    repo = db.Column(db.String(200), nullable=False)
    graph = db.Column(db.Integer, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.String(50), db.ForeignKey('user.email'), nullable=False)

    def __repr__(self):
        return f"User('{self.title}', '{self.date_posted}')"


# ====================================================================================
# routes - these map URLs to your python functions
# ====================================================================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    flash('New entry was successfully posted')
    return redirect(url_for('table'))

@app.route('/form', methods=['GET', 'POST'])
def form():
    errors = []
    exists = False
    if request.method == 'POST':
        title = request.form.get('title')
        if len(title) < 3:
            errors.append( 'Please choose a title (at least 3 letters long)' )

        text = request.form.get('text')

        author = request.form.get('Author')

        filename = request.form.get('Filename')

        repository = request.form.get('repo')
        repo = git_parser.urlClone(repository)
        temp = db.session.query(Post).filter_by(repo=repository).first()

        graph = int(request.form.get('graph'))
        if graph not in [1,2,3,4]:
            errors.append('please choose a graph type')

        # if no errors
        if len(errors) == 0:


            # if repository does not already exist
            if temp is None:
                db.session.add(Post(title=title, description=text, repo=repository, graph=graph,
                                    date_posted=datetime.utcnow(), user_id=session['username']))
                db.session.commit()
                flash('Your entry "' + title + '" was saved to the database')
                gc.collect()

            if graph is 1:
                git_parser.getTotalCommits(repo, 15)
                return render_template('average_graph.html')
            elif graph is 2:
                git_parser.getAuthorHistory(repo, author, datetime(1, 1, 1), datetime.utcnow())
                return render_template('AuthorHistory.html')
            elif graph is 3:
                git_parser.getAuthors(repo, 15)
                return render_template('average_graph2.html')
            elif graph is 4:
                git_parser.getFileHistory(repo, filename, datetime(1, 1, 1), datetime.utcnow())
                return render_template('graph4.html')
            else:
                flash('Please select a graph type')
                return render_template('form.html')

    return render_template('form.html')


@app.route('/graph')
def graph():

    return render_template('graph.html')


@app.route('/browse',methods=['POST', 'GET'])
def browse():

    query_result = db.session.query(Post).all()
    return render_template('browse.html', list=query_result)


@app.route('/delete', methods=['POST'])
def delete():

    item = request.form['delete_item']
    Post.query.filter_by(title=item).delete()
    db.session.commit()
    query_result = db.session.query(Post).all()
    return render_template('browse.html', list=query_result)


@app.route('/search', methods=['POST', 'GET'])
def search():

    item = request.form['search_item']
    query_result = Post.query.filter_by(title=item).first()
    return render_template('browse.html', list=[query_result])


@app.route('/percentage_graph')
def percentage_graph():
    return render_template('percentage_graph.html')

@app.route('/authhistory_graph')
def authhistory_graph():
    return render_template('authhistory_graph.html')


@app.route('/average_graph')
def average_graph():
    return render_template('average_graph.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        u = db.session.query(User).filter_by(username=request.form['username']).first()
        if u is not None:
            p = u.password

            if not pbkdf2_sha256.verify(request.form['password'], p):
                error = "Invalid password"

            else:
                session['logged_in'] = True
                session['username'] = u.username
                flash('You were logged in as ' + session['username'])
                return redirect(url_for('index'))
        else:
            error = "Invalid Credentials"

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('index'))


class RegistrationForm(Form):
    username = TextField('Username', [validators.Length(min=4, max=20)])
    email = TextField('Email Address', [validators.Length(min=10, max=50)])
    password = PasswordField('Name', [validators.Length(min=8, max=30)])


@app.route('/register', methods=["GET", "POST"])
def register():
    try:
        form = RegistrationForm(request.form)

        if request.method == "POST" and form.validate():
            username = form.username.data
            email = form.email.data
            password = form.password.data
            hashpass = pbkdf2_sha256.hash(password)

            x = db.session.query(User.username).filter_by(username=username).first()

            if x is not None:
                flash("That username already exists, please try again.")
                return render_template('register.html', form=form)

            else:
                db.session.add(User(email=email, username=username, password=hashpass))

                db.session.commit()
                flash("Registration Successful")
                gc.collect()

                session['logged_in'] = True
                session['username'] = username

                return redirect(url_for('index'))

        return render_template("register.html", form=form)

    except Exception as e:
        return (str(e))

@app.after_request
def clearcache(response):
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response

# ====================================================================================
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


# ====================================================================================
if __name__ == '__main__':
    app.run()
# ====================================================================================


