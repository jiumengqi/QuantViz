# -*- coding: utf-8 -*-
"""
课程相关数据模型
"""
from datetime import datetime
from db import db


class Course(db.Model):
    """课程模型"""
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    instructor = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.String(50), nullable=False)
    level = db.Column(db.String(20), nullable=False)  # 初级、中级、高级
    category = db.Column(db.String(50), nullable=False)  # basic, pricing, risk, portfolio, quant
    rating = db.Column(db.Float, default=0.0)
    description = db.Column(db.Text)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # 关系
    lessons = db.relationship('Lesson', backref='course', lazy='dynamic')
    
    def __repr__(self):
        return f'<Course {self.title}>'


class Lesson(db.Model):
    """课程章节模型"""
    __tablename__ = 'lessons'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    order = db.Column(db.Integer, nullable=False)  # 章节顺序
    duration = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text)
    video_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Lesson {self.title}>'


class CourseResource(db.Model):
    """课程资源模型"""
    __tablename__ = 'course_resources'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    resource_type = db.Column(db.String(50))  # ppt, code, paper, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CourseResource {self.name}>'


class UserCourse(db.Model):
    """用户课程关联模型（用于记录用户报名的课程）"""
    __tablename__ = 'user_courses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed = db.Column(db.Boolean, default=False)
    progress = db.Column(db.Integer, default=0)  # 完成进度百分比
    
    def __repr__(self):
        return f'<UserCourse user_id={self.user_id} course_id={self.course_id}>'


class CourseRating(db.Model):
    """课程评价模型"""
    __tablename__ = 'course_ratings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5星
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CourseRating user_id={self.user_id} course_id={self.course_id} rating={self.rating}>'
