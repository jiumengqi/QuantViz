# -*- coding: utf-8 -*-
"""统一错误处理装饰器"""
from functools import wraps
from flask import jsonify, current_app
from db import db


def api_error_handler(func):
    """API路由统一错误处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except PermissionError as e:
            return jsonify({'error': str(e)}), 403
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"[{func.__name__}] {e}", exc_info=True)
            return jsonify({'error': '服务器内部错误'}), 500
    return wrapper
