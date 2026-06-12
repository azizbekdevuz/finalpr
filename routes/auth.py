from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import models.user as UserModel

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """회원가입 뷰."""
    if 'user_id' in session:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        # 유효성 검사
        errors = []
        if not username or len(username) < 3:
            errors.append('사용자명은 3자 이상이어야 합니다.')
        if not email or '@' not in email:
            errors.append('올바른 이메일을 입력해주세요.')
        if len(password) < 6:
            errors.append('비밀번호는 6자 이상이어야 합니다.')
        if password != confirm:
            errors.append('비밀번호가 일치하지 않습니다.')
        if UserModel.username_exists(username):
            errors.append('이미 사용 중인 사용자명입니다.')
        if UserModel.email_exists(email):
            errors.append('이미 사용 중인 이메일입니다.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('auth/register.html',
                                   username=username, email=email)

        UserModel.create_user(username, email, password)
        flash('회원가입이 완료되었습니다! 로그인해주세요.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """로그인 뷰."""
    if 'user_id' in session:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = UserModel.find_by_username(username)
        if user and UserModel.verify_password(user, password):
            session.permanent = True
            session['user_id']  = str(user['_id'])
            session['username'] = user['username']
            session['role']     = user.get('role', 'user')
            flash(f'환영합니다, {user["username"]}님!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        else:
            flash('사용자명 또는 비밀번호가 올바르지 않습니다.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    """로그아웃 뷰."""
    session.clear()
    flash('로그아웃되었습니다.', 'info')
    return redirect(url_for('main.index'))
