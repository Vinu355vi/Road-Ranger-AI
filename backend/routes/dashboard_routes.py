from flask import Blueprint, render_template

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/')
def index():
    return render_template('index.html')

@dashboard.route('/dashboard')
def dashboard_view():
    return render_template('dashboard.html')
