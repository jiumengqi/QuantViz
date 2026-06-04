from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for, flash
from flask_login import login_required, current_user
from services.models.pricing.black_scholes import calculate_bs
# 暂时注释掉，因为services.models.risk模块中不存在var_calculator
# from services.models.risk import var_calculator
import pandas as pd
from datetime import datetime
from db import db

# 创建课程模块蓝图
courses_bp = Blueprint('courses', __name__)


@courses_bp.route('/')
def courses_index():
    """课程首页"""
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

    # 推荐课程
    featured_courses = Course.query.filter_by(is_active=True).order_by(Course.rating.desc()).limit(3).all()

    return render_template(
        'courses/index.html',
        categories=course_categories,
        featured_courses=featured_courses
    )


@courses_bp.route('/<string:category>')
def course_category(category):
    """课程分类页面"""
    # 导入课程模型
    from services.models.courses import Course
    
    # 获取分类名称
    category_name = {
        'basic': '基础知识',
        'pricing': '资产定价',
        'risk': '风险管理',
        'portfolio': '投资组合',
        'quant': '量化策略'
    }.get(category, '全部课程')

    # 从数据库获取对应分类的课程
    courses = Course.query.filter_by(category=category, is_active=True).order_by(Course.rating.desc()).all()

    return render_template(
        'courses/category.html',
        category=category,
        category_name=category_name,
        courses=courses
    )


@courses_bp.route('/lesson/<int:course_id>')
def course_lesson(course_id):
    """课程详情页面"""
    # 导入课程模型
    from services.models.courses import Course, Lesson, CourseResource
    
    # 从数据库获取课程数据
    course = Course.query.get(course_id)
    if not course:
        flash('课程不存在', 'danger')
        return redirect(url_for('courses.courses_index'))
    
    # 获取课程的课时
    lessons = Lesson.query.filter_by(course_id=course_id, is_active=True).order_by(Lesson.order).all()
    
    # 获取课程资源
    resources = CourseResource.query.filter_by(course_id=course_id, is_active=True).all()

    return render_template('courses/lesson.html', course=course, lessons=lessons, resources=resources)


@courses_bp.route('/practice/<string:model_type>')
def practice(model_type):
    """实践练习页面"""
    # 根据模型类型展示不同的实践内容
    if model_type == 'black-scholes':
        return render_template('courses/practice_black_scholes.html')
    elif model_type == 'var':
        return render_template('courses/practice_var.html')
    elif model_type == 'markowitz':
        return render_template('courses/practice_markowitz.html')
    else:
        return render_template('courses/practice_general.html', model_type=model_type)


@courses_bp.route('/api/practice/verify', methods=['POST'])
def verify_practice():
    """验证练习答案API"""
    try:
        data = request.json
        model_type = data.get('model_type')
        user_answer = data.get('answer')

        # 根据模型类型验证答案
        if model_type == 'black-scholes':
            # 计算正确答案
            correct_result = calculate_bs(
                spot=float(data.get('params').get('spot')),
                strike=float(data.get('params').get('strike')),
                time=float(data.get('params').get('time')),
                rate=float(data.get('params').get('rate')) / 100,
                volatility=float(data.get('params').get('volatility')) / 100,
                option_type=data.get('params').get('option_type')
            )

            # 检查用户答案是否在可接受范围内（允许一定误差）
            is_correct = abs(float(user_answer) - correct_result['price']) < 0.5

            return jsonify({
                'is_correct': is_correct,
                'correct_answer': round(correct_result['price'], 2),
                'explanation': '期权价格计算正确！' if is_correct else f'计算有误，正确结果应为{round(correct_result["price"], 2)}'
            })

        # 其他模型的验证逻辑...
        return jsonify({'is_correct': False, 'message': '验证功能正在开发中'})

    except Exception as e:
        current_app.logger.error(f"练习验证失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


@courses_bp.route('/api/courses/search', methods=['GET'])
def search_courses():
    """搜索课程API"""
    try:
        query = request.args.get('q', '')
        category = request.args.get('category', '')
        
        # 导入课程模型
        from services.models.courses import Course
        
        # 构建查询
        course_query = Course.query.filter_by(is_active=True)
        
        # 应用分类过滤
        if category:
            course_query = course_query.filter_by(category=category)
        
        # 应用搜索过滤
        if query:
            course_query = course_query.filter(
                (Course.title.ilike(f'%{query}%')) | 
                (Course.instructor.ilike(f'%{query}%')) |
                (Course.description.ilike(f'%{query}%'))
            )
        
        # 执行查询
        courses = course_query.order_by(Course.rating.desc()).all()
        
        # 格式化结果
        results = []
        for course in courses:
            results.append({
                'id': course.id,
                'title': course.title,
                'instructor': course.instructor,
                'category': course.category,
                'rating': course.rating,
                'students': course.students_count or 0
            })
        
        return jsonify({
            'success': True,
            'results': results,
            'total': len(results)
        })
        
    except Exception as e:
        current_app.logger.error(f"课程搜索失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@courses_bp.route('/enroll/<int:course_id>', methods=['POST'])
@login_required
def enroll_course(course_id):
    """报名课程"""
    try:
        # 导入课程模型
        from services.models.courses import Course, UserCourse
        
        # 检查课程是否存在
        course = Course.query.get(course_id)
        if not course:
            flash('课程不存在', 'danger')
            return redirect(url_for('courses.courses_index'))
        
        # 检查用户是否已经报名
        existing_enrollment = UserCourse.query.filter_by(
            user_id=current_user.id,
            course_id=course_id
        ).first()
        
        if existing_enrollment:
            flash('您已经报名了该课程', 'info')
            return redirect(url_for('courses.course_lesson', course_id=course_id))
        
        # 创建报名记录
        new_enrollment = UserCourse(
            user_id=current_user.id,
            course_id=course_id,
            enrolled_at=datetime.utcnow()
        )
        
        # 保存到数据库
        db.session.add(new_enrollment)
        db.session.commit()
        
        flash('报名成功！', 'success')
        return redirect(url_for('courses.course_lesson', course_id=course_id))
        
    except Exception as e:
        current_app.logger.error(f"课程报名失败: {str(e)}")
        flash('报名失败，请稍后重试', 'danger')
        return redirect(url_for('courses.courses_index'))


@courses_bp.route('/favorite/<int:course_id>', methods=['POST'])
@login_required
def favorite_course(course_id):
    """收藏课程"""
    try:
        # 实际应用中应将课程添加到用户收藏列表
        # 这里仅做模拟
        
        return jsonify({
            'success': True,
            'message': '课程已添加到收藏列表'
        })
        
    except Exception as e:
        current_app.logger.error(f"收藏课程失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@courses_bp.route('/rate/<int:course_id>', methods=['POST'])
@login_required
def rate_course(course_id):
    """评价课程"""
    try:
        data = request.json
        rating = data.get('rating')
        comment = data.get('comment')
        
        # 实际应用中应保存评价到数据库
        # 这里仅做模拟
        
        return jsonify({
            'success': True,
            'message': '评价提交成功'
        })
        
    except Exception as e:
        current_app.logger.error(f"评价课程失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
