from flask import Flask, session, flash, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
app=Flask(__name__)
app.secret_key='secretkey'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db=SQLAlchemy(app)

class User(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100))
    email=db.Column(db.String(100),unique=True)
    password=db.Column(db.String(100))

#to initialize db with app context
with app.app_context():
    db.create_all()
@app.route('/')
def home():
    
    return render_template('home.html')


@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='post':
        name=request.form['name']
        email=request.form['email']
        password=request.form['password']
        confirm_password=request.form['confirm_password']

        if not name or len(name.strip())<2:
            flash('name must be 2 characters long','error')
            return redirect(url_for('register'))
        if not email or '@' not in email:
            flash('email must contain @','error')
            return redirect(url_for('register'))
        if not password or len(password)<8 or not any(char.isdigit() for char in password) or not any(char.isalpha() for char in password) or not any(not char.isalnum() for char in password):
            flash('password must be 8 char long and must conatin alphabets, digits and special characters','error')
            return redirect(url_for('register'))
        if password != confirm_password:
            flash('Password does not match','error')
            return redirect(url_for('register'))

         #check if user exists
        existing_user= User.query.filter_by(email=email).first()
        if existing_user:
           flash('Email already registered,Please Login')
           return redirect(url_for('login'))

           new_user=User(
             name= name,
             email=email,
             password=generate_password_hash(password))
        try:
          db.session.add(new_user)
          db.session.commit()
          flash('Registeration successful! Please log in.', 'success')
        except Exception as e:
          db.session.rollback()
          flash('An error occurred during registration. Please try again.','error')
          return redirect(url_for('register'))
    
        flash('name must be 2 characters long','error')
    return render_template('register.html')

@app.route('/login')
def login():
    if request.method =='POST':
        email= request.form['email']
        password= request.form['password']
        user=User.query.filter_by(email=email).first()

        if user and confirm_password_hash(user.password,password):
            session['user_id']=user.id
            session['user_name']=user.name
            flash('login successful!','success')
            return redirect(url_for('index'))
        else:
            flash('invalid email or password.', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')

if __name__=='__main__':
    app.run(debug=True)


            






    

