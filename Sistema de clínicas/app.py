from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave-secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

paciente_profissional = db.Table('paciente_profissional',
    db.Column('paciente_id', db.Integer, db.ForeignKey('paciente.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

# 🏥 Modelo da Clínica
class Clinic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)

    users = db.relationship('User', back_populates='clinic')
    pacientes = db.relationship('Paciente', back_populates='clinic')

# 👤 Modelo do Usuário
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    credits = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False)

    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'))
    clinic = db.relationship('Clinic', back_populates='users')

    pacientes = db.relationship('Paciente', secondary=paciente_profissional, back_populates='profissionais')

# 👶 Modelo do Paciente
class Paciente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    responsavel = db.Column(db.String(150), nullable=False)

    # 🔗 Vinculo com clínica
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=False)
    clinic = db.relationship('Clinic', back_populates='pacientes')

    # 🔗 Relacionamento com os profissionais (usuários)
    profissionais = db.relationship('User', secondary=paciente_profissional, back_populates='pacientes')

    def __repr__(self):
        return f'<Paciente {self.nome}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Login inválido. Verifique usuário e senha.')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Usuário já existe!')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)  # ✅ Correto
        new_user = User(username=username, password=hashed_password, credits=0, is_admin=False)
        
        db.session.add(new_user)
        db.session.commit()

        flash('Usuário criado com sucesso!')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/tools')
@login_required
def tools():
    if current_user.credits <= 0:
        flash('Você não tem créditos suficientes. Abasteça seus créditos.')
        return redirect(url_for('dashboard'))
    return render_template('tools.html')

@app.route('/meus_pacientes')
@login_required
def meus_pacientes():
    pacientes = current_user.pacientes  # por causa do relacionamento many-to-many
    return render_template('meus_pacientes.html', pacientes=pacientes)

@app.route('/paciente/<int:paciente_id>')
@login_required
def detalhes_paciente(paciente_id):
    paciente = Paciente.query.get_or_404(paciente_id)
    if paciente not in current_user.pacientes and not current_user.is_admin:
        flash("Acesso não autorizado a este paciente.")
        return redirect(url_for('dashboard'))
    return render_template('detalhes_paciente.html', paciente=paciente)

@app.route('/paciente/<int:paciente_id>/montar_relatorio')
@login_required
def montar_relatorio(paciente_id):
    return f'Montar relatório para paciente {paciente_id}'

@app.route('/paciente/<int:paciente_id>/relatorios_anteriores')
@login_required
def relatorios_anteriores(paciente_id):
    return f'Consultar relatórios de {paciente_id}'

@app.route('/paciente/<int:paciente_id>/adicionar_teste')
@login_required
def adicionar_teste(paciente_id):
    return f'Adicionar teste ao paciente {paciente_id}'

@app.route('/paciente/<int:paciente_id>/testes_anteriores')
@login_required
def testes_anteriores(paciente_id):
    return f'Consultar testes anteriores de {paciente_id}'

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# -------------------------
# 🔥 Área de Administração
# -------------------------
@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Acesso não autorizado.')
        return redirect(url_for('dashboard'))

    users = User.query.all()
    return render_template('admin.html', users=users)


@app.route('/admin/update_credits/<int:user_id>', methods=['POST'])
@login_required
def update_credits(user_id):
    if not current_user.is_admin:
        flash('Acesso não autorizado.')
        return redirect(url_for('dashboard'))

    user = User.query.get(user_id)
    try:
        new_credits = int(request.form['credits'])
        user.credits = new_credits
        db.session.commit()
        flash(f'Créditos atualizados para {user.username}.')
    except:
        flash('Erro ao atualizar créditos.')

    return redirect(url_for('admin'))


@app.route('/admin/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('Acesso não autorizado.')
        return redirect(url_for('dashboard'))

    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash(f'Usuário {user.username} deletado.')
    return redirect(url_for('admin'))

@app.route('/admin/add_clinic', methods=['GET', 'POST'])
@login_required
def add_clinic():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form['name']
        if Clinic.query.filter_by(name=name).first():
            flash('Essa clínica já existe!')
        else:
            new_clinic = Clinic(name=name)
            db.session.add(new_clinic)
            db.session.commit()
            flash('Clínica cadastrada com sucesso!')
        return redirect(url_for('add_clinic'))

    clinics = Clinic.query.all()
    return render_template('add_clinic.html', clinics=clinics)

@app.route('/admin/assign_user', methods=['GET', 'POST'])
@login_required
def assign_user():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))

    users = User.query.filter_by(is_admin=False).all()
    clinics = Clinic.query.all()

    if request.method == 'POST':
        user_id = request.form['user_id']
        clinic_id = request.form['clinic_id']

        user = User.query.get(user_id)
        user.clinic_id = clinic_id
        db.session.commit()

        flash('Usuário atribuído à clínica com sucesso!')
        return redirect(url_for('assign_user'))

    return render_template('assign_user.html', users=users, clinics=clinics)

@app.route('/add_paciente', methods=['GET', 'POST'])
@login_required
def add_paciente():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))

    clinics = Clinic.query.all()
    users = User.query.all()

    if request.method == 'POST':
        nome = request.form['nome']
        idade = request.form['idade']
        responsavel = request.form['responsavel']
        clinic_id = request.form['clinic']
        profissionais_ids = request.form.getlist('profissionais')

        paciente = Paciente(
            nome=nome,
            idade=idade,
            responsavel=responsavel,
            clinic_id=clinic_id
        )

        for prof_id in profissionais_ids:
            user = User.query.get(int(prof_id))
            paciente.profissionais.append(user)

        db.session.add(paciente)
        db.session.commit()
        return redirect(url_for('admin'))

    return render_template('add_paciente.html', clinics=clinics, users=users)

@app.route('/admin/pacientes')
@login_required
def admin_pacientes():
    if not current_user.is_admin:
        flash("Acesso não autorizado.")
        return redirect(url_for('dashboard'))

    pacientes = Paciente.query.all()
    return render_template('admin_pacientes.html', pacientes=pacientes)

@app.route('/admin/paciente/<int:paciente_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_paciente(paciente_id):
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))

    paciente = Paciente.query.get_or_404(paciente_id)
    clinics = Clinic.query.all()
    users = User.query.filter_by(is_admin=False).all()

    if request.method == 'POST':
        paciente.nome = request.form['nome']
        paciente.idade = request.form['idade']
        paciente.responsavel = request.form['responsavel']
        paciente.clinic_id = request.form['clinic']

        # Limpa e atualiza os profissionais
        paciente.profissionais.clear()
        for user_id in request.form.getlist('profissionais'):
            profissional = User.query.get(int(user_id))
            paciente.profissionais.append(profissional)

        db.session.commit()
        flash('Paciente atualizado com sucesso!')
        return redirect(url_for('admin_pacientes'))

    return render_template('editar_paciente.html', paciente=paciente, clinics=clinics, users=users)

@app.route('/admin/paciente/<int:paciente_id>/deletar')
@login_required
def deletar_paciente(paciente_id):
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))

    paciente = Paciente.query.get_or_404(paciente_id)
    db.session.delete(paciente)
    db.session.commit()
    flash('Paciente deletado com sucesso.')
    return redirect(url_for('admin_pacientes'))

if not os.path.exists('database.db'):
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password=generate_password_hash('admin'),
                is_admin=True,
                credits=0
            )
            db.session.add(admin)
            db.session.commit()

    app.run(debug=True)
