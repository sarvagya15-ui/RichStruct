from flask import Flask, render_template, request, redirect, url_for, flash 
from flask_login import LoginManager, login_user, logout_user, login_required, 
current_user 
from models import db, User, Schema, ActivityLog 
from utils import generate_product_jsonld, generate_faq_jsonld, 
generate_course_jsonld 
from rule_engine import validate_schema_rules 
import json 
import os 
app = Flask(__name__) 
app.config['SECRET_KEY'] = 'production-secret-123' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
db.init_app(app) 
# Login Configuration 
login_manager = LoginManager() 
login_manager.login_view = 'login' 
login_manager.init_app(app) 
@login_manager.user_loader 
def load_user(user_id): 
return db.session.get(User, int(user_id)) 
# DB Initialization 
with app.app_context(): 
db.create_all() 
# --- Module 15: Global Activity Logging helper --- 
def log_action(action): 
if current_user.is_authenticated: 
log = ActivityLog(action=action, user_id=current_user.id) 
db.session.add(log) 
db.session.commit() 
# --- ROUTES --- 
 
@app.route('/') 
def index(): 
    return render_template('index.html') 
 
@app.route('/register', methods=['GET', 'POST']) 
def register(): 
    if current_user.is_authenticated: 
        return redirect(url_for('index')) 
    if request.method == 'POST': 
        username, email, password = request.form.get('username'), 
request.form.get('email'), request.form.get('password') 
        if User.query.filter((User.username == username) | (User.email == email)).first(): 
            flash('User already exists.', 'danger') 
            return redirect(url_for('register')) 
        new_user = User(username=username, email=email) 
        new_user.set_password(password) 
        db.session.add(new_user) 
        db.session.commit() 
        flash('Account created! Please login.', 'success') 
        return redirect(url_for('login')) 
    return render_template('register.html') 
 
@app.route('/login', methods=['GET', 'POST']) 
def login(): 
    if request.method == 'POST': 
        user = User.query.filter_by(username=request.form.get('username')).first() 
        if user and user.check_password(request.form.get('password')): 
            login_user(user) 
            log_action("User logged in") 
            flash(f'Welcome back, {user.username}!', 'success') 
            return redirect(url_for('index')) 
        flash('Invalid credentials.', 'danger') 
    return render_template('login.html') 
 
@app.route('/logout') 
@login_required 
def logout(): 
    log_action("User logged out") 
    logout_user() 
    return redirect(url_for('login')) 
 
@app.route('/generate') 
@login_required 
def select_schema(): 
    schema_types = [ 
        {'id': 'product', 'name': 'Product', 'desc': 'Rich snippets for E-commerce.', 'icon': 'fa
shopping-cart'}, 
        {'id': 'faq', 'name': 'FAQ', 'desc': 'Questions and answers.', 'icon': 'fa-question-circle'}, 
        {'id': 'course', 'name': 'Course', 'desc': 'Educational content.', 'icon': 'fa-graduation
cap'} 
    ] 
    return render_template('generate.html', schema_types=schema_types) 
 
@app.route('/generate/<schema_type>') 
@login_required 
def create_schema(schema_type): 
    return render_template(f'forms/{schema_type}.html', type=schema_type) 
 
@app.route('/generate_jsonld/<schema_type>', methods=['POST']) 
@login_required 
def generate_jsonld(schema_type): 
    json_result = {} 
    name_for_storage = "" 
    if schema_type == 'product': 
        json_result = generate_product_jsonld(request.form) 
        name_for_storage = f"Product: {request.form.get('name')}" 
    elif schema_type == 'faq': 
        q, a = request.form.getlist('question[]'), request.form.getlist('answer[]') 
        json_result = generate_faq_jsonld(q, a) 
        name_for_storage = f"FAQ: {q[0][:30]}..." if q else "Empty FAQ" 
    elif schema_type == 'course': 
        json_result = generate_course_jsonld(request.form) 
        name_for_storage = f"Course: {request.form.get('name')}" 
 
    json_string = json.dumps(json_result, indent=4) 
    new_schema = Schema(schema_type=schema_type, 
schema_name=name_for_storage,  
                        json_content=json_string, user_id=current_user.id) 
    db.session.add(new_schema) 
    log_action(f"Generated {schema_type} schema: {name_for_storage}") 
    db.session.commit() 
    return render_template('result.html', json_data=json_string, 
schema_type=schema_type) 
 
@app.route('/history') 
@login_required 
def history(): 
    user_schemas = 
Schema.query.filter_by(user_id=current_user.id).order_by(Schema.created_at.desc()).a
ll() 
    return render_template('history.html', schemas=user_schemas) 
 
@app.route('/activity') 
@login_required 
def activity_log(): 
    logs = 
ActivityLog.query.filter_by(user_id=current_user.id).order_by(ActivityLog.created_at.des
c()).all() 
    return render_template('activity.html', logs=logs) 
 
@app.route('/validate', methods=['GET', 'POST']) 
@login_required 
def validate(): 
    validation_report = None 
    input_json = "" 
    if request.method == 'POST': 
        input_json = request.form.get('json_content') 
        try: 
            parsed_data = json.loads(input_json) 
            errors, warnings = validate_schema_rules(parsed_data) 
            score = max(0, 100 - (len(errors)*20) - (len(warnings)*10)) 
            log_action(f"Validated Schema (Score: {score})") 
            validation_report = { 
                'status': 'error' if errors else ('warning' if warnings else 'success'), 
                'message': 'Compliance Report', 'details': f"Found {len(errors)} errors and 
{len(warnings)} tips.", 
                'errors': errors, 'warnings': warnings, 'score': score, 
                'error_count': len(errors), 'warning_count': len(warnings) 
            } 
        except: 
            validation_report = {'status': 'error', 'message': 'Invalid JSON!', 'score': 0, 
'error_count': 1} 
    return render_template('validate.html', report=validation_report, 
input_json=input_json) 
 
if __name__ == '__main__': 
    app.run(debug=True, port=5000)