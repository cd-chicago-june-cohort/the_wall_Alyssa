from flask import Flask, session, request, redirect, render_template, flash
from mysqlconnection import MySQLConnector
import md5
import re

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

app = Flask(__name__)
app.secret_key = '04c46b3b62477fc999e63d62c635d97c'
mysql = MySQLConnector(app, 'the_wall')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registration', methods = ['POST'])
def register():
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    password = md5.new(request.form['password']).hexdigest()
    data = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'password': password
    }
    errors=True
    query = 'select * from users where email = :email'
    db_check = mysql.query_db(query, data)
    # Check to see if user is already in database
    if len(db_check) == 1:
        flash("This e-mail address is already registered with The Wall.  Please try logging in, or register with a different e-mail address")
    # Validations and error messages
    elif len(first_name) < 1 or len(last_name) < 1 or len(email) < 1 or len(request.form['password']) < 1:
        flash("All fields are required!")
    elif not EMAIL_REGEX.match(email):
        flash("Invalid Email Address!")
    else:
        errors=False
    # if not in database AND no errors, update database, set session id and go to the wall
    if errors:
        return redirect('/')
    else:
        insert = 'insert into users (first_name, last_name, email, password, created_at) values(:first_name, :last_name, :email, :password, NOW())'
        session['id'] = mysql.query_db(insert, data)
        return redirect ('/wall')

@app.route('/authenticate', methods = ['POST'])
def authenticate():
    email = request.form['email']
    password = md5.new(request.form['password']).hexdigest()
    data = {
        'email': email,
        'password': password
    }
    errors=True
    query = 'select * from users where email = :email'
    db_check = mysql.query_db(query, data)
    # Validations and error messages
    if not EMAIL_REGEX.match(email):
        flash("Invalid Email Address!")
    elif len(db_check) != 1:
        flash("E-mail address not registered.  Please register an account")
    elif len(email) < 1 or len(request.form['password']) < 1:
        flash("All fields are required!")
    elif db_check[0]['password'] != password:
        flash('Incorrect password, please try again')
    else:
        errors=False
    # no errors, set session id, login and go to the wall
    if errors:
        return redirect('/')
    else:
        session['id'] = db_check[0]['id']
        return redirect ('/wall')

@app.route('/wall')
def wall():
    # get info about which user is logged in
    user_id = session['id']
    query = 'select first_name from users where id = :user_id'
    data = {'user_id': user_id}
    user_name = mysql.query_db(query, data)
    name = user_name[0]['first_name']
    # get data from MySQL for all messages
    query = 'select concat(first_name, " ", last_name) as name, date_format(messages.created_at, "%b %D %Y") as date, message, messages.created_at, messages.id from messages join users on user_id=users.id order by created_at desc'
    all_messages = mysql.query_db(query)
    query = 'select concat(first_name, " ", last_name) as name, date_format(messages.created_at, "%b %D %Y") as date, comment, comments.created_at, message_id from comments join messages on message_id=messages.id join users on comments.user_id= users.id order by created_at'
    all_comments = mysql.query_db(query)
    return render_template('wall.html', name = name, all_messages = all_messages, all_comments = all_comments)    

@app.route('/post_message', methods = ['POST'])
def post_message():
    message = request.form['message']
    user_id = session['id']
    insert = "insert into messages (user_id, message, created_at) values (:user_id, :message, NOW())" 
    data = {
        'user_id' : user_id,
        'message' : message
    }
    mysql.query_db(insert, data)
    return redirect('/wall')

@app.route('/post_comment/<message_id>', methods = ['POST'])
def post_comment(message_id):
    comment = request.form['comment']
    user_id = session['id']
    insert = 'insert into comments (user_id, message_id, comment, created_at) values (:user_id, :message_id, :comment, NOW())'
    data = {
        'user_id': user_id,
        'message_id': message_id,
        'comment': comment
    }
    mysql.query_db(insert, data)
    return redirect('/wall')

@app.route('/logout')
def logout():
    session.clear()
    return redirect ('/')

app.run(debug=True)