from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_exists = User.query.filter((User.username == username) | (User.email == email)).first()
        if user_exists:
            flash('Username or email already exists.', 'danger')
            return redirect(url_for('register'))
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            log_action("User logged in")
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login failed. Check your username and password.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/generate')
@login_required
def select_schema():
    schema_types = [
        {'id': 'product', 'name': 'Product', 'desc': 'E-commerce products with price and reviews.', 'icon': 'fa-shopping-cart'},
        {'id': 'faq', 'name': 'FAQ', 'desc': 'Frequently asked questions and answers.', 'icon': 'fa-question-circle'},
        {'id': 'course', 'name': 'Course', 'desc': 'Educational courses with details and providers.', 'icon': 'fa-graduation-cap'}
    ]
    return render_template('generate.html', schema_types=schema_types)

@app.route('/generate/<schema_type>')
@login_required
def create_schema(schema_type):
    valid_types = ['product', 'faq', 'course']
    if schema_type not in valid_types:
        flash('Invalid schema type selected.', 'danger')
        return redirect(url_for('select_schema'))
    
    return render_template(f'forms/{schema_type}.html', type=schema_type)

from models import db, User, Schema, ActivityLog
from utils import generate_product_jsonld, generate_faq_jsonld, generate_course_jsonld
import json

def log_action(action):
    if current_user.is_authenticated:
        log = ActivityLog(action=action, user_id=current_user.id)
        db.session.add(log)
        db.session.commit()

@app.route('/generate_jsonld/<schema_type>', methods=['POST'])
@login_required
def generate_jsonld(schema_type):
    json_result = {}
    name_for_storage = ""
    
    if schema_type == 'product':
        json_result = generate_product_jsonld(request.form)
        name_for_storage = f"Product: {request.form.get('name')}"
    
    elif schema_type == 'faq':
        questions = request.form.getlist('question[]')
        answers = request.form.getlist('answer[]')
        json_result = generate_faq_jsonld(questions, answers)
        name_for_storage = f"FAQ: {questions[0][:50]}..." if questions else "Empty FAQ"
        
    elif schema_type == 'course':
        json_result = generate_course_jsonld(request.form)
        name_for_storage = f"Course: {request.form.get('name')}"

    # Convert dictionary to formatted JSON string
    json_string = json.dumps(json_result, indent=4)
    
    # Save to Database
    new_schema = Schema(
        schema_type=schema_type,
        schema_name=name_for_storage,
        json_content=json_string,
        user_id=current_user.id
    )
    db.session.add(new_schema)
    
    # Log Activity
    log_action(f"Generated {schema_type} schema: {name_for_storage}")
    
    db.session.commit()
    
    return render_template('result.html', 
                          json_data=json_string, 
                          schema_type=schema_type)

@app.route('/history')
@login_required
def history():
    user_schemas = Schema.query.filter_by(user_id=current_user.id).order_by(Schema.created_at.desc()).all()
    return render_template('history.html', schemas=user_schemas)

@app.route('/activity')
@login_required
def activity_log():
    logs = ActivityLog.query.filter_by(user_id=current_user.id).order_by(ActivityLog.created_at.desc()).limit(50).all()
    return render_template('activity.html', logs=logs)

from rule_engine import validate_schema_rules

@app.route('/validate', methods=['GET', 'POST'])
@login_required
def validate():
    validation_report = None
    input_json = ""
    
    if request.method == 'POST':
        input_json = request.form.get('json_content')
        try:
            # Step 1: Basic Syntax Check
            parsed_data = json.loads(input_json)
            
            # Step 2: Rule-Based Validation (Module 10)
            errors, warnings = validate_schema_rules(parsed_data)
            
            # Calculate Score (Basic heuristic: Start at 100, -20 for each error, -10 for each warning)
            score = 100 - (len(errors) * 20) - (len(warnings) * 10)
            score = max(0, score) # Don't go below 0
            
            # Log Activity
            log_action(f"Validated JSON schema (Score: {score})")
            
            if not errors and not warnings:
                validation_report = {
                    'status': 'success',
                    'message': 'Perfect! Your schema is production-ready.',
                    'details': 'Valid JSON syntax and 100% compliance with Google guidelines.',
                    'errors': [],
                    'warnings': [],
                    'error_count': 0,
                    'warning_count': 0,
                    'score': 100
                }
            else:
                status = 'error' if errors else 'warning'
                validation_report = {
                    'status': status,
                    'message': 'Schema Compliance Report',
                    'details': f"Analysis complete. Found {len(errors)} critical issues and {len(warnings)} recommendations.",
                    'errors': errors,
                    'warnings': warnings,
                    'error_count': len(errors),
                    'warning_count': len(warnings),
                    'score': score
                }

        except json.JSONDecodeError as e:
            validation_report = {
                'status': 'error',
                'message': 'Syntax Error Found!',
                'details': f"Error: {str(e)}",
                'errors': [f"Invalid JSON format. Check for missing commas or quotes."],
                'warnings': []
            }
            
    return render_template('validate.html', report=validation_report, input_json=input_json)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
