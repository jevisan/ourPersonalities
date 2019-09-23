from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app, make_response, session, send_from_directory

from flask_login import current_user, login_user, logout_user
from flask_login import login_required

from werkzeug.urls import url_parse

import os

from app import db
from app.main.forms import RequestAnalysisForm, LoginForm, RegistrationForm
from app.models import User, Task, Result
from app.main import bp

from time import time
from datetime import datetime


def validatetotask():
    """
    State of request
    1. No ongoing task
    2. Task in progress
    3. Previous task failed
    """
    p_status = 1
    if current_user.get_task_in_progress("analyze_user"):
        p_status = 2
    if current_user.get_task_failed():
        p_status = 3
    return p_status


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Credenciales no validas')
            return redirect(url_for('main.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('login.html', title='Log In', form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Usuario {} registrado con exito'.format(user.username))
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Registro', form=form)


@bp.route('/')
def welcome():
    return render_template('welcome.html')


@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = RequestAnalysisForm()
    if form.validate_on_submit():
        user_tag = form.user_tag.data
        return redirect(url_for('main.analyze_user', usertag=user_tag))
    return render_template('index.html', title='Our Personalities', form=form)


@bp.route('/analyze_user/<usertag>')
@login_required
def analyze_user(usertag):

    proceed = validatetotask()
    if proceed is 1:
        message = "Sin info de task"
        print(message)
    elif proceed is 2:
        message = "Analisis en proceso"
        print(message)
    elif proceed is 3:
        message = "Analisis previo fallido"
        print(message)

    # NO HAY ID DE UN TASK O TASK PASADO FALLO
    if proceed is 1 or proceed is 3:
        # SE LANZA EL TASK A COLA DE REDIS
        current_user.launch_task('analyze_user', 'Analizando usuario', user_tag=usertag)
        # task = launch_task('analyze_user', 'Analizando usuario', user=usertag, user_ip=user_ip, timeout='60m')
        # task = launch_task('example', 'Analizando usuario', seconds=10, timeout='60m')
        db.session.commit()
        # un redirect a una vista de "estamos analizando sus tuits"
        return redirect(url_for('main.analyzing'))

    # VISTA DE PROGRESO DEL ANALISIS
    # return render_template('user_analysis.html', title='Analisis de usuario', proceed_status=proceed, message=message)


@bp.route('/analyzing')
@login_required
def analyzing():
    return render_template('analyzing.html', title='Analisis de personalidad en proceso')


@bp.route('/analysis_results/<task>')
@login_required
def analysis_results(task):
    t = Task.query.get(task)
    result = Result.query.get(task)
    data = result.get_data()
    session['task_id'] = task
    return render_template('analysis_results.html', data=data)


@bp.route('/get_analysis_results')
def get_analysis_results():
    analysis_result = Result.query.get(session['task_id'])
    session.pop('task_id', None)
    data = analysis_result.get_data()

    nodes_data = [{
        'avatar': data['user_avatar'],
        'name': data['user_screen_name'],
        'user': data['user'],
        'personality': data['user_personality'],
    }]

    for f in data['friends']:
        f_dic = {
            'avatar': f['avatar'],
            'distance': f['distance'],
            'personality': f['personality'],
            'name': f['name']
        }
        nodes_data.append(f_dic)
    return jsonify(nodes_data)


@bp.route('/acerca')
def acerca():
    files_folder = os.path.dirname(os.path.abspath(__file__)) + '/../static/files/'
    return send_from_directory(files_folder, 'Vigil_Santos_Jorge_Documento_PT3.pdf', as_attachment=True)

@bp.route('/demo')
def demo():
    results = Result.query.all()
    demos = {}
    for r in results:
        data = r.get_data()
        demos[r.id] = data['user_screen_name']
    return render_template('demo.html', title='ourPersonalities Demo', demos=demos)
