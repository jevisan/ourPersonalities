from datetime import datetime
from hashlib import md5
import json
from time import time
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login

import redis
import rq

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    tasks = db.relationship('Task', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)


    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


    def launch_task(self, name, description, *args, **kwargs):
        rq_job = current_app.task_queue.enqueue('app.tasks.' + name, self.id, *args, **kwargs)

        task = Task(id=rq_job.get_id(), name=name, description=description, user=self)
        db.session.add(task)            # A LA BASE DE DATOS
        return task


    def get_tasks_in_progress(self):
        return Task.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return Task.query.filter_by(name=name, user=self, complete=False).first()

    def get_task_failed(self):
        return Task.query.filter_by(user=self, completed_with_status=500).first()

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Task(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    complete = db.Column(db.Boolean, default=False)
    completed_with_status = db.Column(db.Integer, default=None)

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_job(self):
        job = self.get_rq_job()
        return job

    def get_progress(self):
        job = self.get_rq_job()
        # return job.meta.get('progress', 0) if job is not None else 100
        return job.meta.get('progress', 0)

    def get_status(self):
        job = self.get_rq_job()
        return job.meta.get('status_description', '') if job is not None else ''


class Result(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    result = db.Column(db.Text)

    def get_data(self):
        return json.loads(str(self.result))
