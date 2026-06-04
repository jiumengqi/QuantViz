# -*- coding: utf-8 -*-
"""
认证模块
"""
import os
import sys

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 将项目根目录添加到Python路径中
project_dir = os.path.abspath(os.path.join(current_dir, '../'))
if project_dir not in sys.path:
    sys.path.append(project_dir)

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from datetime import datetime
import re
import time
import json
import logging
from werkzeug.utils import secure_filename
from services.models.user import User
from services.models.operation_log import OperationLog
from db import db

# 创建日志记录器
logger = logging.getLogger(__name__)

# 创建认证蓝图
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # 获取表单数据
        username = request.form.get('username')
        password = request.form.get('password')
        remember_me = request.form.get('remember_me') == 'on'
        
        # 验证表单数据
        if not username or not password:
            flash('请输入用户名和密码', 'danger')
            return redirect(url_for('auth.login'))
        
        # 查找用户
        user = User.query.filter_by(username=username).first()
        
        # 检查用户是否存在
        if not user:
            flash('无效的用户名或密码', 'danger')
            return redirect(url_for('auth.login'))
        
        # 检查用户是否被锁定
        if user.is_locked:
            flash('账户已被锁定，请15分钟后再试', 'danger')
            return redirect(url_for('auth.login'))
        
        # 验证密码
        if not user.check_password(password):
            # 增加登录尝试次数
            user.increment_login_attempts()
            flash('无效的用户名或密码', 'danger')
            return redirect(url_for('auth.login'))
        
        # 登录成功，重置登录尝试次数
        user.reset_login_attempts()
        
        # 登录用户
        login_user(user, remember=remember_me)
        
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # 记录操作日志
        OperationLog.log(
            user_id=user.id,
            username=user.username,
            action='登录系统',
            ip_address=request.remote_addr or '',
            details=f'用户 {user.username} 登录成功'
        )
        
        # 获取下一个页面
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index')
        
        flash('登录成功', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # 获取表单数据
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # 验证表单数据
        if not username or not email or not password or not confirm_password:
            flash('请填写所有必填字段', 'danger')
            return redirect(url_for('auth.register'))
        
        # 验证邮箱格式
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
            flash('邮箱格式不正确', 'danger')
            return redirect(url_for('auth.register'))
        
        # 验证密码强度
        if len(password) < 8:
            flash('密码长度至少为8位', 'danger')
            return redirect(url_for('auth.register'))
        if not re.search(r'[A-Z]', password):
            flash('密码至少包含一个大写字母', 'danger')
            return redirect(url_for('auth.register'))
        if not re.search(r'[a-z]', password):
            flash('密码至少包含一个小写字母', 'danger')
            return redirect(url_for('auth.register'))
        if not re.search(r'[0-9]', password):
            flash('密码至少包含一个数字', 'danger')
            return redirect(url_for('auth.register'))
        
        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return redirect(url_for('auth.register'))
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
            return redirect(url_for('auth.register'))
        
        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            flash('邮箱已存在', 'danger')
            return redirect(url_for('auth.register'))
        
        # 创建新用户
        user = User(username=username, email=email)
        user.set_password(password)
        
        # 保存用户到数据库
        db.session.add(user)
        db.session.commit()
        
        # 记录操作日志
        OperationLog.log(
            user_id=user.id,
            username=user.username,
            action='注册账户',
            ip_address=request.remote_addr or '',
            details=f'新用户 {user.username} ({user.email}) 注册成功'
        )
        
        flash('注册成功，请登录', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """用户登出"""
    # 记录操作日志
    OperationLog.log(
        user_id=current_user.id,
        username=current_user.username,
        action='登出系统',
        ip_address=request.remote_addr or '',
        details=f'用户 {current_user.username} 登出'
    )
    logout_user()
    flash('已成功登出', 'success')
    return redirect(url_for('main.index'))


@auth_bp.route('/profile')
@login_required
def profile():
    """用户个人资料"""
    return render_template('auth/profile.html', user=current_user)


@auth_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """编辑用户个人资料"""
    if request.method == 'POST':
        # 获取表单数据
        email = request.form.get('email')
        username = request.form.get('username')
        phone = request.form.get('phone', '')
        bio = request.form.get('bio', '')
        theme_preference = request.form.get('theme_preference', 'light')
        refresh_frequency = request.form.get('refresh_frequency', 5, type=int)
        notification_email = request.form.get('notification_email') == 'on'
        notification_browser = request.form.get('notification_browser') == 'on'
        backtest_default_capital = request.form.get('backtest_default_capital', 100000.0, type=float)
        backtest_default_fee = request.form.get('backtest_default_fee', 0.0003, type=float)
        
        # 验证邮箱格式
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
            flash('邮箱格式不正确', 'danger')
            return redirect(url_for('auth.edit_profile'))
        
        # 检查邮箱是否已被其他用户使用
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != current_user.id:
            flash('邮箱已被其他用户使用', 'danger')
            return redirect(url_for('auth.edit_profile'))
        
        # 检查用户名是否已被其他用户使用
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != current_user.id:
            flash('用户名已被其他用户使用', 'danger')
            return redirect(url_for('auth.edit_profile'))
        
        # 验证电话号码格式（可选）
        if phone and not re.match(r'^1[3-9]\d{9}$', phone):
            flash('电话号码格式不正确', 'danger')
            return redirect(url_for('auth.edit_profile'))
        
        # 验证刷新频率
        if refresh_frequency < 1 or refresh_frequency > 60:
            flash('行情刷新频率应在 1-60 秒之间', 'danger')
            return redirect(url_for('auth.edit_profile'))
        
        # 验证回测默认资金
        if backtest_default_capital < 1000:
            flash('回测默认资金不能少于 1000 元', 'danger')
            return redirect(url_for('auth.edit_profile'))
        
        # 验证回测默认手续费
        if backtest_default_fee < 0 or backtest_default_fee > 0.01:
            flash('回测默认手续费应在 0-1% 之间', 'danger')
            return redirect(url_for('auth.edit_profile'))
        
        # 更新用户信息
        current_user.email = email
        current_user.username = username
        current_user.phone = phone
        current_user.bio = bio
        current_user.theme_preference = theme_preference
        current_user.refresh_frequency = refresh_frequency
        current_user.notification_email = notification_email
        current_user.notification_browser = notification_browser
        current_user.backtest_default_capital = backtest_default_capital
        current_user.backtest_default_fee = backtest_default_fee
        
        # 保存更改
        db.session.commit()
        
        flash('个人资料已更新', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/edit_profile.html', user=current_user)


@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改用户密码"""
    if request.method == 'POST':
        # 获取表单数据
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # 验证当前密码
        if not current_user.check_password(current_password):
            flash('当前密码不正确', 'danger')
            return redirect(url_for('auth.change_password'))
        
        # 验证新密码强度
        if len(new_password) < 8:
            flash('密码长度至少为8位', 'danger')
            return redirect(url_for('auth.change_password'))
        if not re.search(r'[A-Z]', new_password):
            flash('密码至少包含一个大写字母', 'danger')
            return redirect(url_for('auth.change_password'))
        if not re.search(r'[a-z]', new_password):
            flash('密码至少包含一个小写字母', 'danger')
            return redirect(url_for('auth.change_password'))
        if not re.search(r'[0-9]', new_password):
            flash('密码至少包含一个数字', 'danger')
            return redirect(url_for('auth.change_password'))
        
        if new_password != confirm_password:
            flash('两次输入的新密码不一致', 'danger')
            return redirect(url_for('auth.change_password'))
        
        # 设置新密码
        current_user.set_password(new_password)
        db.session.commit()
        
        flash('密码已更新', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html')


@auth_bp.route('/admin')
@login_required
def admin_dashboard():
    """管理员面板"""
    if not current_user.is_admin:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    # 从数据库获取真实统计数据
    from services.models.stock import Strategy, BacktestResult
    from services.models.feedback import Feedback
    
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_strategies = Strategy.query.count()
    total_backtests = BacktestResult.query.count()
    total_feedback = Feedback.query.count()
    pending_feedback = Feedback.query.filter_by(status='pending').count()
    
    # 获取所有用户
    users = User.query.order_by(User.created_at.desc()).all()
    
    dashboard_stats = {
        'total_users': total_users,
        'active_users': active_users,
        'total_strategies': total_strategies,
        'total_backtests': total_backtests,
        'total_feedback': total_feedback,
        'pending_feedback': pending_feedback
    }
    
    return render_template('auth/admin.html', users=users, dashboard_stats=dashboard_stats)


@auth_bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    """请求密码重置"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('请输入邮箱地址', 'danger')
            return redirect(url_for('auth.reset_password_request'))
        
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('该邮箱地址未注册', 'danger')
            return redirect(url_for('auth.reset_password_request'))
        
        # 生成重置令牌
        token = user.generate_reset_token()
        
        # 这里应该发送邮件，现在我们直接显示重置链接
        # 实际应用中应该使用Flask-Mail发送邮件
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        flash(f'请点击以下链接重置密码：{reset_url}', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_request.html')


@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """重置密码"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # 验证令牌
    user = User.verify_reset_token(token)
    if not user:
        flash('无效或过期的令牌', 'danger')
        return redirect(url_for('auth.reset_password_request'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or not confirm_password:
            flash('请填写所有必填字段', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        
        # 验证密码强度
        if len(password) < 8:
            flash('密码长度至少为8位', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        if not re.search(r'[A-Z]', password):
            flash('密码至少包含一个大写字母', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        if not re.search(r'[a-z]', password):
            flash('密码至少包含一个小写字母', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        if not re.search(r'[0-9]', password):
            flash('密码至少包含一个数字', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        
        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        
        # 设置新密码
        user.set_password(password)
        db.session.commit()
        
        flash('密码重置成功，请登录', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', token=token)


@auth_bp.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """编辑用户信息"""
    if not current_user.is_admin:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    user = User.query.get(user_id)
    if not user:
        flash('用户不存在', 'danger')
        return redirect(url_for('auth.admin_dashboard'))
    
    if request.method == 'POST':
        # 获取表单数据
        email = request.form.get('email')
        role = request.form.get('role')
        is_active = request.form.get('is_active') == 'on'
        
        # 验证邮箱格式
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
            flash('邮箱格式不正确', 'danger')
            return redirect(url_for('auth.edit_user', user_id=user_id))
        
        # 检查邮箱是否已被其他用户使用
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user_id:
            flash('邮箱已被其他用户使用', 'danger')
            return redirect(url_for('auth.edit_user', user_id=user_id))
        
        # 更新用户信息
        user.email = email
        user.role = role
        user.is_active = is_active
        
        # 保存更改
        db.session.commit()
        
        # 记录操作日志
        OperationLog.log(
            user_id=current_user.id,
            username=current_user.username,
            action='编辑用户',
            ip_address=request.remote_addr or '',
            details=f'管理员 {current_user.username} 编辑了用户 {user.username} (ID: {user.id})，角色={role}，活跃={is_active}'
        )
        
        flash('用户信息已更新', 'success')
        return redirect(url_for('auth.admin_dashboard'))
    
    return render_template('auth/edit_user.html', user=user)


@auth_bp.route('/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    """删除用户"""
    if not current_user.is_admin:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    user = User.query.get(user_id)
    if not user:
        flash('用户不存在', 'danger')
        return redirect(url_for('auth.admin_dashboard'))
    
    # 不能删除自己
    if user.id == current_user.id:
        flash('不能删除自己的账户', 'danger')
        return redirect(url_for('auth.admin_dashboard'))
    
    # 删除用户
    deleted_username = user.username
    deleted_user_id = user.id
    db.session.delete(user)
    db.session.commit()
    
    # 记录操作日志
    OperationLog.log(
        user_id=current_user.id,
        username=current_user.username,
        action='删除用户',
        ip_address=request.remote_addr or '',
        details=f'管理员 {current_user.username} 删除了用户 {deleted_username} (ID: {deleted_user_id})'
    )
    
    flash('用户已删除', 'success')
    return redirect(url_for('auth.admin_dashboard'))


@auth_bp.route('/toggle_user_status/<int:user_id>')
@login_required
def toggle_user_status(user_id):
    """切换用户启用/禁用状态"""
    if not current_user.is_admin:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    user = User.query.get(user_id)
    if not user:
        flash('用户不存在', 'danger')
        return redirect(url_for('auth.admin_dashboard'))
    
    # 不能禁用自己
    if user.id == current_user.id:
        flash('不能修改自己的账户状态', 'danger')
        return redirect(url_for('auth.admin_dashboard'))
    
    # 切换状态
    user.is_active = not user.is_active
    db.session.commit()
    
    # 记录操作日志
    action = '启用用户' if user.is_active else '禁用用户'
    OperationLog.log(
        user_id=current_user.id,
        username=current_user.username,
        action=action,
        ip_address=request.remote_addr or '',
        details=f'管理员 {current_user.username} {action}: {user.username} (ID: {user.id})'
    )
    
    status_text = '启用' if user.is_active else '禁用'
    flash(f'用户 {user.username} 已{status_text}', 'success')
    return redirect(url_for('auth.admin_dashboard'))


@auth_bp.route('/system_settings')
@login_required
def system_settings():
    """系统设置"""
    if not current_user.is_admin:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    # 获取所有系统配置
    from services.models.stock import SystemConfig
    configs = SystemConfig.query.all()
    
    return render_template('auth/system_settings.html', configs=configs)


@auth_bp.route('/edit_config/<int:config_id>', methods=['GET', 'POST'])
@login_required
def edit_config(config_id):
    """编辑系统配置"""
    if not current_user.is_admin:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    from services.models.stock import SystemConfig
    config = SystemConfig.query.get(config_id)
    if not config:
        flash('配置不存在', 'danger')
        return redirect(url_for('auth.system_settings'))
    
    if request.method == 'POST':
        # 获取表单数据
        value = request.form.get('value')
        description = request.form.get('description')
        is_active = request.form.get('is_active') == 'on'
        
        # 更新配置
        config.value = value
        config.description = description
        config.is_active = is_active
        
        # 保存更改
        db.session.commit()
        
        flash('配置已更新', 'success')
        return redirect(url_for('auth.system_settings'))
    
    return render_template('auth/edit_config.html', config=config)


@auth_bp.route('/add_config', methods=['GET', 'POST'])
@login_required
def add_config():
    """添加系统配置"""
    if not current_user.is_admin:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # 获取表单数据
        key = request.form.get('key')
        value = request.form.get('value')
        description = request.form.get('description')
        is_active = request.form.get('is_active') == 'on'
        
        # 验证配置键是否已存在
        from services.models.stock import SystemConfig
        existing_config = SystemConfig.query.filter_by(key=key).first()
        if existing_config:
            flash('配置键已存在', 'danger')
            return redirect(url_for('auth.add_config'))
        
        # 创建新配置
        new_config = SystemConfig(
            key=key,
            value=value,
            description=description,
            is_active=is_active
        )
        
        # 保存到数据库
        db.session.add(new_config)
        db.session.commit()
        
        # 记录操作日志
        OperationLog.log(
            user_id=current_user.id,
            username=current_user.username,
            action='添加系统配置',
            ip_address=request.remote_addr or '',
            details=f'管理员 {current_user.username} 添加了配置 {key}={value}'
        )
        
        flash('配置已添加', 'success')
        return redirect(url_for('auth.system_settings'))
    
    return render_template('auth/add_config.html')


@auth_bp.route('/delete_config/<int:config_id>')
@login_required
def delete_config(config_id):
    """删除系统配置"""
    if not current_user.is_admin:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    from services.models.stock import SystemConfig
    config = SystemConfig.query.get(config_id)
    if not config:
        flash('配置不存在', 'danger')
        return redirect(url_for('auth.system_settings'))
    
    # 删除配置
    config_key = config.key
    db.session.delete(config)
    db.session.commit()
    
    # 记录操作日志
    OperationLog.log(
        user_id=current_user.id,
        username=current_user.username,
        action='删除系统配置',
        ip_address=request.remote_addr or '',
        details=f'管理员 {current_user.username} 删除了配置 {config_key}'
    )
    
    flash('配置已删除', 'success')
    return redirect(url_for('auth.system_settings'))


@auth_bp.route('/content_management')
@login_required
def content_management():
    """内容管理"""
    if not current_user.is_admin:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    # 导入课程模型
    from services.models.courses import Course
    
    # 课程分类
    course_categories = [
        {'id': 'basic', 'name': '基础知识', 'count': Course.query.filter_by(category='basic', is_active=True).count()},
        {'id': 'pricing', 'name': '资产定价', 'count': Course.query.filter_by(category='pricing', is_active=True).count()},
        {'id': 'risk', 'name': '风险管理', 'count': Course.query.filter_by(category='risk', is_active=True).count()},
        {'id': 'portfolio', 'name': '投资组合', 'count': Course.query.filter_by(category='portfolio', is_active=True).count()},
        {'id': 'quant', 'name': '量化策略', 'count': Course.query.filter_by(category='quant', is_active=True).count()}
    ]
    
    # 从数据库获取课程数据
    featured_courses = Course.query.filter_by(is_active=True).order_by(Course.rating.desc()).limit(3).all()
    
    return render_template('auth/content_management.html', categories=course_categories, courses=featured_courses)


@auth_bp.route('/admin_content')
@login_required
def admin_content():
    """站点内容编辑 - 动态内容管理系统"""
    if not current_user.is_admin:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    return render_template('auth/admin_content.html')


@auth_bp.route('/system_stats')
@login_required
def system_stats():
    """系统统计"""
    if not current_user.is_admin:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    # 从数据库获取真实统计数据
    from services.models.stock import Strategy, BacktestResult, SystemConfig, Stock
    from services.models.feedback import Feedback
    from services.models.community import StrategyShare
    from services.models.courses import Course
    
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_strategies = Strategy.query.count()
    total_backtests = BacktestResult.query.count()
    total_feedback = Feedback.query.count()
    pending_feedback = Feedback.query.filter_by(status='pending').count()
    total_shares = StrategyShare.query.count()
    total_courses = Course.query.count()
    total_configs = SystemConfig.query.count()
    total_stocks = Stock.query.count()
    total_operation_logs = OperationLog.query.count()
    
    # 最近7天新注册用户
    from datetime import timedelta
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    new_users_7d = User.query.filter(User.created_at >= seven_days_ago).count()
    
    # 最近7天活跃用户（登录过的）
    active_users_7d = User.query.filter(User.last_login >= seven_days_ago).count()
    
    stats_data = {
        'total_users': total_users,
        'active_users': active_users,
        'total_strategies': total_strategies,
        'total_backtests': total_backtests,
        'total_feedback': total_feedback,
        'pending_feedback': pending_feedback,
        'total_shares': total_shares,
        'total_courses': total_courses,
        'total_configs': total_configs,
        'total_stocks': total_stocks,
        'total_operation_logs': total_operation_logs,
        'new_users_7d': new_users_7d,
        'active_users_7d': active_users_7d,
        'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return render_template('auth/system_stats.html', stats_data=stats_data)


@auth_bp.route('/operation_logs')
@login_required
def operation_logs():
    """操作日志"""
    if not current_user.is_admin:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 从数据库获取真实操作日志
    pagination = OperationLog.query.order_by(
        OperationLog.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    logs = pagination.items
    total = pagination.total
    pages = pagination.pages
    
    # 日志统计
    from datetime import timedelta
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    
    today_count = OperationLog.query.filter(OperationLog.created_at >= today).count()
    week_count = OperationLog.query.filter(OperationLog.created_at >= week_start).count()
    month_count = OperationLog.query.filter(OperationLog.created_at >= month_start).count()
    
    return render_template('auth/operation_logs.html', 
                         logs=logs, 
                         page=page,
                         pages=pages,
                         total=total,
                         per_page=per_page,
                         today_count=today_count,
                         week_count=week_count,
                         month_count=month_count)


@auth_bp.route('/security_settings')
@login_required
def security_settings():
    """安全设置"""
    if not current_user.is_admin:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    # 模拟安全设置数据
    security_settings = {
        'login_attempt_limit': 5,
        'lockout_duration': 15,  # 分钟
        'password_min_length': 8,
        'require_uppercase': True,
        'require_lowercase': True,
        'require_digit': True,
        'require_special': False
    }
    
    return render_template('auth/security_settings.html', security_settings=security_settings)


@auth_bp.route('/edit_course/<int:course_id>', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    """编辑课程"""
    if not current_user.is_admin:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    # 导入课程模型
    from services.models.courses import Course
    
    # 从数据库获取课程数据
    course = Course.query.get(course_id)
    if not course:
        flash('课程不存在', 'danger')
        return redirect(url_for('auth.content_management'))
    
    # 课程分类
    categories = [
        {'id': 'basic', 'name': '基础知识'},
        {'id': 'pricing', 'name': '资产定价'},
        {'id': 'risk', 'name': '风险管理'},
        {'id': 'portfolio', 'name': '投资组合'},
        {'id': 'quant', 'name': '量化策略'}
    ]
    
    if request.method == 'POST':
        # 获取表单数据
        title = request.form.get('title')
        instructor = request.form.get('instructor')
        duration = request.form.get('duration')
        level = request.form.get('level')
        category = request.form.get('category')
        description = request.form.get('description')
        content = request.form.get('content')
        
        # 验证表单数据
        if not title or not instructor or not duration or not level or not category:
            flash('请填写所有必填字段', 'danger')
            return redirect(url_for('auth.edit_course', course_id=course_id))
        
        # 更新课程数据
        course.title = title
        course.instructor = instructor
        course.duration = duration
        course.level = level
        course.category = category
        course.description = description
        course.content = content
        
        # 保存到数据库
        db.session.commit()
        
        flash('课程已更新', 'success')
        return redirect(url_for('auth.content_management'))
    
    return render_template('auth/edit_course.html', course=course, categories=categories)


@auth_bp.route('/add_course', methods=['GET', 'POST'])
@login_required
def add_course():
    """添加课程"""
    if not current_user.is_admin:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    # 导入课程模型
    from services.models.courses import Course
    
    # 课程分类
    categories = [
        {'id': 'basic', 'name': '基础知识'},
        {'id': 'pricing', 'name': '资产定价'},
        {'id': 'risk', 'name': '风险管理'},
        {'id': 'portfolio', 'name': '投资组合'},
        {'id': 'quant', 'name': '量化策略'}
    ]
    
    if request.method == 'POST':
        # 获取表单数据
        title = request.form.get('title')
        instructor = request.form.get('instructor')
        duration = request.form.get('duration')
        level = request.form.get('level')
        category = request.form.get('category')
        description = request.form.get('description')
        content = request.form.get('content')
        
        # 验证表单数据
        if not title or not instructor or not duration or not level or not category:
            flash('请填写所有必填字段', 'danger')
            return redirect(url_for('auth.add_course'))
        
        # 创建新课程
        new_course = Course(
            title=title,
            instructor=instructor,
            duration=duration,
            level=level,
            category=category,
            description=description,
            content=content
        )
        
        # 保存到数据库
        db.session.add(new_course)
        db.session.commit()
        
        # 记录操作日志
        OperationLog.log(
            user_id=current_user.id,
            username=current_user.username,
            action='添加课程',
            ip_address=request.remote_addr or '',
            details=f'管理员 {current_user.username} 添加了课程 {title}'
        )
        
        flash('课程已添加', 'success')
        return redirect(url_for('auth.content_management'))
    
    return render_template('auth/add_course.html', categories=categories)


@auth_bp.route('/delete_course/<int:course_id>')
@login_required
def delete_course(course_id):
    """删除课程"""
    if not current_user.is_admin:
        flash('您没有权限访问此页面', 'danger')
        return redirect(url_for('main.index'))
    
    # 导入课程模型
    from services.models.courses import Course
    
    # 从数据库获取课程
    course = Course.query.get(course_id)
    if not course:
        flash('课程不存在', 'danger')
        return redirect(url_for('auth.content_management'))
    
    # 删除课程
    course_title = course.title
    db.session.delete(course)
    db.session.commit()
    
    # 记录操作日志
    OperationLog.log(
        user_id=current_user.id,
        username=current_user.username,
        action='删除课程',
        ip_address=request.remote_addr or '',
        details=f'管理员 {current_user.username} 删除了课程 {course_title}'
    )
    
    flash('课程已删除', 'success')
    return redirect(url_for('auth.content_management'))


# 允许的头像文件扩展名
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_upload_folder():
    """获取头像上传目录"""
    # 获取项目根目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.abspath(os.path.join(current_dir, '../../'))
    upload_dir = os.path.join(project_dir, 'static/uploads/avatars')
    # 确保目录存在
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    return upload_dir


@auth_bp.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    """上传用户头像"""
    if 'avatar' not in request.files:
        return jsonify({'success': False, 'message': '没有上传文件'}), 400
    
    file = request.files['avatar']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': '不支持的文件格式，请上传 jpg、png 或 gif 格式'}), 400
    
    # 检查文件大小
    file.seek(0, 2)  # 移到文件末尾
    file_size = file.tell()
    file.seek(0)  # 恢复到文件开头
    
    if file_size > MAX_FILE_SIZE:
        return jsonify({'success': False, 'message': '文件大小超过 2MB 限制'}), 400
    
    try:
        # 获取文件扩展名
        ext = file.filename.rsplit('.', 1)[1].lower()
        # 生成新文件名: avatar_{user_id}_{timestamp}.{ext}
        filename = f"avatar_{current_user.id}_{int(time.time())}.{ext}"
        
        # 保存文件
        upload_dir = get_upload_folder()
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        # 删除旧头像（如果存在且不是默认头像）
        if current_user.avatar and current_user.avatar != 'default.png':
            old_filepath = os.path.join(upload_dir, current_user.avatar)
            if os.path.exists(old_filepath):
                os.remove(old_filepath)
        
        # 更新用户头像
        current_user.avatar = filename
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': '头像上传成功',
            'avatar_url': url_for('auth.get_avatar', filename=filename)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'上传失败：{str(e)}'}), 500


@auth_bp.route('/avatars/<filename>')
def get_avatar(filename):
    """获取用户头像"""
    upload_dir = get_upload_folder()
    return send_from_directory(upload_dir, filename)


# ========== 用户设置管理路由 ==========

@auth_bp.route('/user_settings')
@login_required
def user_settings():
    """用户偏好设置页面"""
    from services.models.stock import UserSettings
    
    # 获取或创建用户设置
    settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.session.add(settings)
        db.session.commit()
    
    return render_template('auth/user_settings.html', settings=settings)


@auth_bp.route('/api/user_settings', methods=['GET'])
@login_required
def get_user_settings():
    """获取用户设置API"""
    from services.models.stock import UserSettings
    
    try:
        settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not settings:
            # 返回默认设置
            return jsonify({
                'success': True,
                'settings': {
                    'theme': 'light',
                    'language': 'zh-CN',
                    'refresh_interval': 5,
                    'default_start_date': '2020-01-01',
                    'default_end_date': '2024-12-31',
                    'default_initial_capital': 1000000.0,
                    'default_commission': 0.0003,
                    'notification_email': True,
                    'notification_browser': False,
                    'favorite_indices': [],
                    'favorite_sectors': []
                }
            })
        
        return jsonify({
            'success': True,
            'settings': {
                'id': settings.id,
                'theme': settings.theme,
                'language': settings.language,
                'refresh_interval': settings.refresh_interval,
                'default_start_date': settings.default_start_date,
                'default_end_date': settings.default_end_date,
                'default_initial_capital': settings.default_initial_capital,
                'default_commission': settings.default_commission,
                'notification_email': settings.notification_email,
                'notification_browser': settings.notification_browser,
                'favorite_indices': json.loads(settings.favorite_indices) if settings.favorite_indices else [],
                'favorite_sectors': json.loads(settings.favorite_sectors) if settings.favorite_sectors else []
            }
        })
    except Exception as e:
        logger.error(f"获取用户设置失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/api/user_settings', methods=['POST'])
@login_required
def save_user_settings():
    """保存用户设置API"""
    from services.models.stock import UserSettings
    
    try:
        data = request.json
        
        # 获取或创建用户设置
        settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not settings:
            settings = UserSettings(user_id=current_user.id)
            db.session.add(settings)
        
        # 更新设置
        if 'theme' in data:
            settings.theme = data['theme']
        if 'language' in data:
            settings.language = data['language']
        if 'refresh_interval' in data:
            settings.refresh_interval = int(data['refresh_interval'])
        if 'default_start_date' in data:
            settings.default_start_date = data['default_start_date']
        if 'default_end_date' in data:
            settings.default_end_date = data['default_end_date']
        if 'default_initial_capital' in data:
            settings.default_initial_capital = float(data['default_initial_capital'])
        if 'default_commission' in data:
            settings.default_commission = float(data['default_commission'])
        if 'notification_email' in data:
            settings.notification_email = bool(data['notification_email'])
        if 'notification_browser' in data:
            settings.notification_browser = bool(data['notification_browser'])
        if 'favorite_indices' in data:
            settings.favorite_indices = json.dumps(data['favorite_indices']) if isinstance(data['favorite_indices'], list) else data['favorite_indices']
        if 'favorite_sectors' in data:
            settings.favorite_sectors = json.dumps(data['favorite_sectors']) if isinstance(data['favorite_sectors'], list) else data['favorite_sectors']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '设置已保存'
        })
    except Exception as e:
        logger.error(f"保存用户设置失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/api/user_settings/reset', methods=['POST'])
@login_required
def reset_user_settings():
    """重置用户设置为默认值"""
    from services.models.stock import UserSettings
    
    try:
        # 删除现有设置
        settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if settings:
            db.session.delete(settings)
            db.session.commit()
        
        # 创建新的默认设置
        settings = UserSettings(user_id=current_user.id)
        db.session.add(settings)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '设置已重置为默认值'
        })
    except Exception as e:
        logger.error(f"重置用户设置失败: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== 管理员 API 路由 ==========

@auth_bp.route('/admin/api/stats')
@login_required
def admin_api_stats():
    """返回管理员实时统计数据"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    from datetime import timedelta
    from services.models.stock import Strategy, BacktestResult, SystemConfig
    from services.models.feedback import Feedback
    from services.models.community import StrategyShare
    
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_users = User.query.filter(User.created_at >= today).count()
    today_ops = OperationLog.query.filter(OperationLog.created_at >= today).count()
    
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_strategies = Strategy.query.count()
    total_backtests = BacktestResult.query.count()
    total_shares = StrategyShare.query.count()
    total_feedback = Feedback.query.count()
    pending_feedback = Feedback.query.filter_by(status='pending').count()
    
    # 系统运行状态检查
    db_connected = True
    try:
        db.session.execute(db.text('SELECT 1'))
    except Exception:
        db_connected = False
    
    system_status = 'normal' if db_connected else 'warning'
    
    return jsonify({
        'success': True,
        'stats': {
            'total_users': total_users,
            'active_users': active_users,
            'total_strategies': total_strategies,
            'total_backtests': total_backtests,
            'total_shares': total_shares,
            'total_feedback': total_feedback,
            'pending_feedback': pending_feedback,
            'today_new_users': today_users,
            'today_operations': today_ops,
            'system_status': system_status,
            'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    })


@auth_bp.route('/admin/api/users/search')
@login_required
def admin_api_users_search():
    """用户搜索API - 支持分页、搜索、筛选"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '', type=str).strip()
    role = request.args.get('role', '', type=str).strip()
    status = request.args.get('status', '', type=str).strip()
    
    query = User.query
    
    # 搜索过滤
    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )
    
    # 角色过滤
    if role == 'admin':
        query = query.filter_by(role='admin')
    elif role == 'user':
        query = query.filter_by(role='user')
    
    # 状态过滤
    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'disabled':
        query = query.filter_by(is_active=False)
    
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    users_list = []
    for u in pagination.items:
        users_list.append({
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'role': u.role,
            'is_active': u.is_active,
            'is_admin': u.is_admin,
            'created_at': u.created_at.strftime('%Y-%m-%d %H:%M') if u.created_at else '',
            'last_login': u.last_login.strftime('%Y-%m-%d %H:%M') if u.last_login else '从未登录',
            'avatar': u.avatar or '',
            'login_attempts': u.login_attempts
        })
    
    return jsonify({
        'success': True,
        'users': users_list,
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page,
        'per_page': per_page
    })


@auth_bp.route('/admin/api/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def admin_api_user_detail(user_id):
    """用户详情API - 获取/更新/删除"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'is_active': user.is_active,
                'is_admin': user.is_admin,
                'phone': user.phone or '',
                'bio': user.bio or '',
                'avatar': user.avatar or '',
                'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else '',
                'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '',
                'login_attempts': user.login_attempts,
                'theme_preference': user.theme_preference or 'light',
                'notification_email': user.notification_email,
                'notification_browser': user.notification_browser
            }
        })
    
    elif request.method == 'PUT':
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400
        
        # 不能修改自己
        if user.id == current_user.id:
            return jsonify({'success': False, 'message': '不能通过API修改自己的账户'}), 400
        
        if 'email' in data:
            email = data['email'].strip()
            if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
                return jsonify({'success': False, 'message': '邮箱格式不正确'}), 400
            existing = User.query.filter_by(email=email).first()
            if existing and existing.id != user_id:
                return jsonify({'success': False, 'message': '邮箱已被其他用户使用'}), 400
            user.email = email
        
        if 'role' in data and data['role'] in ('user', 'admin'):
            user.role = data['role']
        
        if 'is_active' in data:
            user.is_active = bool(data['is_active'])
        
        if 'username' in data:
            username = data['username'].strip()
            if username and username != user.username:
                existing = User.query.filter_by(username=username).first()
                if existing:
                    return jsonify({'success': False, 'message': '用户名已被使用'}), 400
                user.username = username
        
        db.session.commit()
        
        OperationLog.log(
            user_id=current_user.id,
            username=current_user.username,
            action='编辑用户',
            ip_address=request.remote_addr or '',
            details=f'管理员 {current_user.username} 通过API编辑了用户 {user.username} (ID: {user.id})'
        )
        
        return jsonify({'success': True, 'message': '用户信息已更新'})
    
    elif request.method == 'DELETE':
        if user.id == current_user.id:
            return jsonify({'success': False, 'message': '不能删除自己的账户'}), 400
        
        deleted_username = user.username
        deleted_user_id = user.id
        db.session.delete(user)
        db.session.commit()
        
        OperationLog.log(
            user_id=current_user.id,
            username=current_user.username,
            action='删除用户',
            ip_address=request.remote_addr or '',
            details=f'管理员 {current_user.username} 通过API删除了用户 {deleted_username} (ID: {deleted_user_id})'
        )
        
        return jsonify({'success': True, 'message': f'用户 {deleted_username} 已删除'})


@auth_bp.route('/admin/api/feedbacks/search')
@login_required
def admin_api_feedbacks_search():
    """反馈搜索API"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    from services.models.feedback import Feedback
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status', '', type=str).strip()
    
    query = Feedback.query
    if status:
        query = query.filter_by(status=status)
    
    pagination = query.order_by(Feedback.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    feedbacks_list = []
    for f in pagination.items:
        feedbacks_list.append({
            'id': f.id,
            'title': f.title,
            'type': f.type,
            'content': f.content[:200] if f.content else '',
            'status': f.status,
            'username': f.user.username if f.user else '未知用户',
            'user_id': f.user_id,
            'admin_reply': f.admin_reply,
            'created_at': f.created_at.strftime('%Y-%m-%d %H:%M') if f.created_at else '',
            'updated_at': f.updated_at.strftime('%Y-%m-%d %H:%M') if f.updated_at else ''
        })
    
    return jsonify({
        'success': True,
        'feedbacks': feedbacks_list,
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page,
        'per_page': per_page
    })


@auth_bp.route('/admin/api/configs', methods=['GET', 'POST'])
@login_required
def admin_api_configs():
    """系统配置API - 获取/更新"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    from services.models.stock import SystemConfig
    
    if request.method == 'GET':
        configs = SystemConfig.query.all()
        configs_list = []
        for c in configs:
            configs_list.append({
                'id': c.id,
                'key': c.key,
                'value': c.value,
                'description': c.description or '',
                'is_active': c.is_active,
                'updated_at': c.updated_at.strftime('%Y-%m-%d %H:%M:%S') if c.updated_at else ''
            })
        
        return jsonify({
            'success': True,
            'configs': configs_list
        })
    
    elif request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400
        
        key = data.get('key', '').strip()
        value = data.get('value', '').strip()
        
        if not key:
            return jsonify({'success': False, 'message': '配置键不能为空'}), 400
        
        config = SystemConfig.query.filter_by(key=key).first()
        if config:
            config.value = value
        else:
            config = SystemConfig(
                key=key,
                value=value,
                description=data.get('description', '')
            )
            db.session.add(config)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'配置 {key} 已保存'})
