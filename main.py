from flask import Flask, render_template, redirect, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_restful import abort
import os
import sqlalchemy
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec
from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, BooleanField, IntegerField
from wtforms.validators import DataRequired
import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import PasswordField
from wtforms.fields.html5 import EmailField
from flask import render_template, url_for, request


SqlAlchemyBase = dec.declarative_base()
__factory = None


def global_init(db_file):
    global __factory
    if __factory:
        return
    if not db_file or not db_file.strip():
        raise Exception("Необходимо указать файл базы данных.")
    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    print(f"Подключение к базе данных по адресу {conn_str}")
    engine = sqlalchemy.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)
    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()


class AddSiteForm(FlaskForm):
    site_address = StringField('URL сайта', validators=[DataRequired()])
    site_name = StringField('Название сайта', validators=[DataRequired()])
    id_topic = IntegerField('Тема сайта')
    site_description = StringField('Описание сайта', validators=[DataRequired()])
    submit = SubmitField('Записать')


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_login = sqlalchemy.Column(sqlalchemy.String, nullable=False, unique=True)
    email = sqlalchemy.Column(sqlalchemy.String, nullable=False, unique=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    age = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    registration_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    topic = orm.relation("Topic", back_populates='user')
    site = orm.relation("Site", back_populates='user')

    def __repr__(self):
        return f"<User> №: {self.id} Почта: {self.email} " \
               f"Возраст: {self.email} Дата регистрации: {self.registration_date}"

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)


class Site(SqlAlchemyBase):
    __tablename__ = 'sites'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    id_user = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    site_address = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    site_name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    id_topic = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("topics.id"))
    date_added = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    site_description = sqlalchemy.Column(sqlalchemy.String)
    topic = orm.relation('Topic')
    user = orm.relation('User')

    def __repr__(self):
        return f'<Site> URL {self.site_address} - {self.site_name}'


class Topic(SqlAlchemyBase):
    __tablename__ = 'topics'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    topic_title = sqlalchemy.Column(sqlalchemy.String)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    user = orm.relation('User')
    site = orm.relation("Site", back_populates='topic')

    def __repr__(self):
        return f'<Topic> {str(self.id) }, {self.topic_title}'


class AddSiteForm(FlaskForm):
    site_address = StringField('URL сайта', validators=[DataRequired()])
    site_name = StringField('Название сайта', validators=[DataRequired()])
    id_topic = IntegerField('Тема сайта')
    site_description = StringField('Описание сайта', validators=[DataRequired()])
    submit = SubmitField('Записать')


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegisterForm(FlaskForm):
    login = StringField('Логин', validators=[DataRequired()])
    email = EmailField('Электронная почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    age = StringField('Возраст', validators=[DataRequired()])
    submit = SubmitField('Запомнить')


class AddTopicForm(FlaskForm):
    topic_title = StringField('Наименование темы', validators=[DataRequired()])
    submit = SubmitField('Запомнить')


app = Flask(__name__)
app.config['SECRET_KEY'] = 'U74anllYYrxWwqcwImKh8LaGFdb8uM'

login_manager = LoginManager()
login_manager.init_app(app)


def main():
    global_init("best_links.sqlite")

    @login_manager.user_loader
    def load_user(user_id):
        session = create_session()
        return session.query(User).get(user_id)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            session = create_session()
            user = session.query(User).filter(User.email == form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                return redirect(f'/{0}/{0}')
            return render_template('login.html', message="Неверный логин или пароль", form=form,
                                   link=url_for('static', filename='css/style.css'))
        return render_template('login.html', title='Авторизация', form=form,
                               link=url_for('static', filename='css/style.css'))

    @app.route("/<int:id_topic>/<int:id_all>")
    @app.route("/index/<int:id_topic>/<int:id_all>")
    def index(id_topic, id_all):
        id_list_users = [1]
        if current_user.is_authenticated:
            if current_user.id != 1:
                if id_all:
                    id_list_users = [current_user.id]
                else:
                    id_list_users.append(current_user.id)
        session = create_session()
        sites = session.query(Site).filter(Site.id_user.in_(id_list_users))
        if id_all:
            id_list_users = [1, current_user.id]
        topics = session.query(Topic).filter(Topic.user_id.in_(id_list_users))
        list_topics = sorted([p for p in topics], key=lambda q: q.topic_title)
        name_topics = {}
        name_topics[0] = 'Все темы сайтов'
        for topic in list_topics:
            if topic.id not in name_topics:
                name_topics[topic.id] = topic.topic_title
            elif topic.id == current_user.id:
                name_topics[topic.id] = topic.topic_title
        dict_site = {}
        list_sites = sorted([p for p in sites], key=lambda q: name_topics[q.id_topic])
        count_sites = {}
        count_sites[0] = len(list_sites)
        for p in list_sites:
            dict_site[p.id_topic] = dict_site.get(p.id_topic, []) + [p]
        for p in dict_site:
            count_sites[p] = len(dict_site[p])
        count_sites[-1] = len(dict_site)
        return render_template("index.html", dict_site=dict_site, name_topics=name_topics,
                               title='Лучшие сайты, отобранные вручную!', id_topic=id_topic,
                               id_all=id_all, count_sites=count_sites)

    @app.route("/")
    @app.route("/index/")
    @app.route("/start/")
    def start():
        id_topic, id_all = 0, 0
        id_list_users = [1]
        if current_user.is_authenticated:
            if current_user.id != 1:
                if id_all:
                    id_list_users = [current_user.id]
                else:
                    id_list_users.append(current_user.id)
        session = create_session()
        sites = session.query(Site).filter(Site.id_user.in_(id_list_users))
        if id_all:
            id_list_users = [1, current_user.id]
        topics = session.query(Topic).filter(Topic.user_id.in_(id_list_users))
        list_topics = sorted([p for p in topics], key=lambda q: q.topic_title)
        name_topics = {}
        name_topics[0] = 'Все темы сайтов'
        for topic in list_topics:
            if topic.id not in name_topics:
                name_topics[topic.id] = topic.topic_title
            elif topic.id == current_user.id:
                name_topics[topic.id] = topic.topic_title
        dict_site = {}
        list_sites = sorted([p for p in sites], key=lambda q: name_topics[q.id_topic])
        count_sites = {}
        count_sites[0] = len(list_sites)
        for p in list_sites:
            dict_site[p.id_topic] = dict_site.get(p.id_topic, []) + [p]
        for p in dict_site:
            count_sites[p] = len(dict_site[p])
        count_sites[-1] = len(dict_site)
        return render_template("index.html", dict_site=dict_site, name_topics=name_topics,
                               title='Лучшие сайты, отобранные вручную!', id_topic=id_topic,
                               id_all=id_all, count_sites=count_sites, link=url_for('static', filename='css/style.css'))

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(f'/{0}/{0}')

    @app.route('/register', methods=['GET', 'POST'])
    def reqister():
        form = RegisterForm()
        if form.validate_on_submit():
            if form.password.data != form.password_again.data:
                return render_template('register.html', title='Регистрация', form=form,
                                       message="Пароли не совпадают", link=url_for('static', filename='css/style.css'))
            session = create_session()
            if session.query(User).filter(User.email == form.email.data).first():
                return render_template('register.html', title='Регистрация', form=form,
                                       message="Этот пользователь уже существует",
                                       link=url_for('static', filename='css/style.css'))
            user = User(
                user_login=form.login.data,
                email=form.email.data,
                age=form.age.data
            )
            user.set_password(form.password.data)
            session.add(user)
            session.commit()
            return redirect('/login')
        return render_template('register.html', title='Регистрация', form=form,
                               link=url_for('static', filename='css/style.css'))

    @app.route('/0/add_site', methods=['GET', 'POST'])
    def add_site():
        add_form = AddSiteForm()
        if add_form.validate_on_submit():
            session = create_session()
            site = Site(
                id_user=current_user.id,
                site_address=add_form.site_address.data.lower(),
                site_name=add_form.site_name.data,
                id_topic=add_form.id_topic.data,
                site_description=add_form.site_description.data
            )
            session.add(site)
            session.commit()
            return redirect(f'/{0}/{0}')
        session = create_session()
        if current_user.is_authenticated:
            topics = session.query(Topic).filter(Topic.user_id.in_([1, current_user.id]))
        else:
            topics = session.query(Topic).filter(Topic.user_id == 1)
        list_topics = sorted([p for p in topics], key=lambda q: q.topic_title)
        return render_template('add_site.html', title='Добавление сайта', form=add_form, list_topics=list_topics,
                               nid=0, link=url_for('static', filename='css/style.css'))

    @app.route('/site/<int:id>', methods=['GET', 'POST'])
    @login_required
    def site_edit(id):
        form = AddSiteForm()
        if request.method == "GET":
            session = create_session()
            sites = session.query(Site).filter((Site.id == id)).first()
            if sites:
                form.site_address.data = sites.site_address
                form.site_name.data = sites.site_name
                form.id_topic.data = sites.id_topic
                form.site_description.data = sites.site_description
            else:
                abort(404)
        if form.validate_on_submit():
            session = create_session()
            sites = session.query(Site).filter((Site.id == id)).first()
            if sites:
                sites.site_address = form.site_address.data
                sites.site_name = form.site_name.data
                sites.id_topic = form.id_topic.data
                sites.site_description = form.site_description.data
                session.commit()
                return redirect(f'/{0}/{0}')
            else:
                abort(404)
        session = create_session()
        if current_user.is_authenticated:
            topics = session.query(Topic).filter(Topic.user_id.in_([1, current_user.id]))
        else:
            topics = session.query(Topic).filter(Topic.user_id == 1)
        list_topics = sorted([p for p in topics], key=lambda q: q.topic_title)
        return render_template('add_site.html', title='Редактирование сайта', form=form, list_topics=list_topics,
                               nid=sites.id_topic, link=url_for('static', filename='css/style.css'))

    @app.route('/site_delete/<int:id>', methods=['GET', 'POST'])
    @login_required
    def site_delete(id):
        session = create_session()
        site = session.query(Site).filter((Site.id == id)).first()
        if site:
            session.delete(site)
            session.commit()
        else:
            abort(404)
        return redirect(f'/{0}/{0}')

    @app.route('/0/add_topic', methods=['GET', 'POST'])
    def add_topic():
        add_form = AddTopicForm()
        if add_form.validate_on_submit():
            session = create_session()
            topic = Topic(
                topic_title=add_form.topic_title.data,
                user_id=current_user.id
            )
            session.add(topic)
            session.commit()
            return redirect(f'/{0}/{0}')
        return render_template('add_topic.html', title='Добавление темы', form=add_form,
                               link=url_for('static', filename='css/style.css'))

    @app.route("/0/topics")
    def topics():
        session = create_session()
        if current_user.is_authenticated:
            topics = session.query(Topic).filter(Topic.user_id.in_([1, current_user.id]))
        else:
            topics = session.query(Topic).filter(Topic.user_id == 1)
        list_topics = sorted([p for p in topics], key=lambda q: q.topic_title)
        return render_template("topics.html", list_topics=list_topics, title='Список тем',
                               link=url_for('static', filename='css/style.css'))

    @app.route('/topics/<int:id>', methods=['GET', 'POST'])
    @login_required
    def topic_edit(id):
        form = AddTopicForm()
        if request.method == "GET":
            session = create_session()
            topic = session.query(Topic).filter(Topic.id == id, Topic.user_id == current_user.id).first()
            if topic:
                form.topic_title.data = topic.topic_title
            else:
                abort(404)
        if form.validate_on_submit():
            session = create_session()
            topic = session.query(Topic).filter(Topic.id == id, Topic.user_id == current_user.id).first()
            if topic:
                topic.topic_title = form.topic_title.data
                session.commit()
                return redirect(f'/{0}/{0}')
            else:
                abort(404)
        return render_template('add_topic.html', title='Редактирование темы', form=form,
                               link=url_for('static', filename='css/style.css'))

    @app.route('/topic_delete/<int:id>', methods=['GET', 'POST'])
    @login_required
    def topic_delete(id):
        session = create_session()
        topic = session.query(Topic).filter(Topic.id == id, Topic.user_id == current_user.id).first()
        site = session.query(Site).filter(Site.id_topic == topic.id).first()
        if site:
            return redirect(f'/{0}/{0}')
        if topic:
            session.delete(topic)
            session.commit()
        else:
            abort(404)
        return redirect(f'/{0}/{0}')

    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)


if __name__ == '__main__':
    main()
