from flask import Blueprint, render_template

# Create blueprint for main routes
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """
    Homepage route - displays bio and personal information
    """
    return render_template('home.html')

@main_bp.route('/contact')
def contact():
    """
    Contact page route - displays contact information
    """
    return render_template('contact.html')

@main_bp.route('/projects')
def projects():
    """
    Projects page route - displays project information
    """
    return render_template('projects.html')