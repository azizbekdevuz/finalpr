from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(f):
    """로그인이 필요한 뷰에 적용하는 데코레이터."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('로그인이 필요한 서비스입니다.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """관리자 권한이 필요한 뷰에 적용하는 데코레이터."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('로그인이 필요한 서비스입니다.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'admin':
            flash('관리자만 접근 가능합니다.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function
