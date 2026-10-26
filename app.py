from flask import Flask, render_template, redirect, url_for, flash, request, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegistrationForm, LoginForm, TransferForm, ChangePasswordForm
from models import db, User, Transaction
from sqlalchemy import text
from datetime import datetime
import os
import secrets

app = Flask(__name__)
# Секреты берутся из переменных окружения; без SECRET_KEY генерируется случайный (сессии сбросятся при рестарте)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///bank.db')
db.init_app(app)
with app.app_context():
    db.create_all()
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    return render_template('home.html')

# Обработчик ошибок для 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Ваш аккаунт успешно создан! Попробуйте войти в него.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('profile'))
        else:
            flash('Не удалось войти в аккаунт. Пожалуйста, проверьте имя пользователя и пароль', 'danger')
    return render_template('login.html', form=form)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    return render_template('profile.html')

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if check_password_hash(current_user.password, form.current_password.data):
            if form.new_password.data == form.confirm_password.data:
                hashed_password = generate_password_hash(form.new_password.data, method='pbkdf2:sha256')
                current_user.password = hashed_password
                db.session.commit()
                flash('Пароль успешно изменен!', 'success')
                return redirect(url_for('profile'))
            else:
                flash('Пароли не совпадают.', 'danger')
        else:
            flash('Текущий пароль неверный.', 'danger')
    return render_template('change_password.html', form=form)


@app.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    form = TransferForm()

    if form.validate_on_submit():
        receiver_username = form.receiver_username.data
        amount = form.amount.data
        query = text(f"SELECT * FROM User WHERE username = '{receiver_username}'")

        receiver = db.session.execute(query).fetchone()

        if receiver:
            if current_user.balance >= float(amount):
                try:
                    receiver_id = receiver[0]
                    update_sender_query = text(
                        f"UPDATE user SET balance = balance - {amount} WHERE id = {current_user.id}")
                    update_receiver_query = text(
                        f"UPDATE user SET balance = balance + {amount} WHERE id = {receiver_id}")

                    db.session.execute(update_sender_query)
                    db.session.execute(update_receiver_query)

                    db.session.commit()

                    timestamp = datetime.utcnow()
                    transaction_query = text(f"""
                        INSERT INTO "transaction" (sender_id, receiver_id, amount, timestamp)
                        VALUES ({current_user.id}, {receiver_id}, {amount}, '{timestamp}')
                    """)
                    db.session.execute(transaction_query)
                    db.session.commit()

                    flash('Перевод произведен успешно', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Ошибка при выполнении перевода: {str(e)}', 'danger')
            else:
                flash('Недостаточно средств', 'danger')
        else:
            flash('Получателя с таким именем не существует', 'danger')

    return render_template('transfer.html', form=form)


@app.route('/transactions', methods=['GET'])
@login_required
def transactions():
    transactions_sent = Transaction.query.filter_by(sender_id=current_user.id).all()
    transactions_received = Transaction.query.filter_by(receiver_id=current_user.id).all()

    return render_template('transactions.html', transactions_sent=transactions_sent, transactions_received=transactions_received)


@app.route('/top-10', methods=['GET'])
def richest():
    top_users = User.query.order_by(User.balance.desc()).limit(10).all()
    return render_template('richest.html', top_users=top_users)


@app.route('/add_money', methods=['GET', 'POST'])
@login_required
def add_money():
    template_string = request.form.get('money', '')

    money = render_template_string(template_string, current_user=current_user)

    current_user.balance += 1
    db.session.commit()
    if money:
        flash(f'Банк не одобрил вам выдачу {money} рублей.', 'success')
    return render_template('earn_money.html', balance=current_user.balance)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 80)), debug=False)
