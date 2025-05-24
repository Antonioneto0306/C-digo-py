# Aqui estamos importando o framework Flask e o SQLAlchemy e suas  dependências
# para criar um aplicativo web e interagir com um banco de dados.
from flask import Flask, render_template, redirect, url_for, session, request, flash

from flask_sqlalchemy import SQLAlchemy

# Aqui estamos criando a aplicação 
app = Flask(__name__)

# Aqui estamos definindo a chave secreta
app.secret_key = 'tentando_nao_ficar_de_exame_muito_menos_dp'

# Aqui estamos fazendo a conexão com o banco de dados MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = \
    '{SGBD}://{usuario}:{senha}@{servidor}/{database}'.format(
        SGBD = 'mysql+mysqlconnector',
        usuario = 'root',
        senha = '3008',
        servidor = 'localhost',
        database = 'prj_work'
     )

# Aqui inicializando o SQLAlchemy com a aplicação Flask
db = SQLAlchemy(app)

# Aqui definimos a tebela de usuários e reservas
class User(db.Model):
    __tablename__ = 'usuario'
    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome_usuario = db.Column(db.String(80), unique=True, nullable=False)
    email_usuario = db.Column(db.String(120), unique=True, nullable=False)
    senha_usuario = db.Column(db.String(255), nullable=False)

    reservas = db.relationship('Reserva', backref='usuario', cascade='all, delete-orphan')


class Reserva(db.Model):
    __tablename__ = 'reservas'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    tipo_espaco = db.Column(db.String(20), nullable=False)
    numero_espaco = db.Column(db.Integer, nullable=False)
    dia = db.Column(db.String(20), nullable=False)
    horario = db.Column(db.String(10), nullable=False)

# Aqui a rota principal para o home.html 
@app.route('/')
def agenda():
    return render_template('home.html')

# Aqui a rota para o login.html
# Fazendo verificaçao se usuário vai para homepage ou se admin vai para o painel de admin 
# Caso contrario nao faz login para acessar os recursos da API
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        usuario = User.query.filter_by(email_usuario=email, senha_usuario=senha).first()

        if usuario:
            session['usuario_logado'] = usuario.email_usuario

            if usuario.email_usuario == 'admin@admin.com':
                return redirect(url_for('painel_admin'))
            else:
                return redirect(url_for('home'))
        else:
            flash('Usuário ou senha inválidos. Tente novamente.')
            return redirect(url_for('login'))

    return render_template('login.html')


# Aqui permite o usuário se cadastrar no sistema
# Fazendo verificaçao se o usuário já existe no banco de dados
@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        confirmar_senha = request.form['confirmar_senha']

        if senha != confirmar_senha:
            flash('As senhas não coincidem. Tente novamente.')
            return redirect(url_for('cadastro'))

        usuario_existente = User.query.filter_by(email_usuario=email).first()

        if usuario_existente:
            flash('E-mail já cadastrado. Tente fazer login ou use outro e-mail.')
            return redirect(url_for('cadastro'))

        novo_usuario = User(
            nome_usuario=nome,
            email_usuario=email,
            senha_usuario=senha
        )

        db.session.add(novo_usuario)
        db.session.commit()

        flash('Cadastro realizado com sucesso!')
        return redirect(url_for('login')) 

    return render_template('cadastrar.html')

# Aqui somente usuario logado pode acessar a homepage
# Caso contrario redireciona para o login
@app.route('/home')
def home():
    if 'usuario_logado' not in session:
        flash('Você precisa estar logado para acessar a Home.')
        return redirect(url_for('home'))
    return render_template('homepage.html')

# Aqui direciona o usuário para a rota de tipos de reservas
# Se salas, teatros ou auditórios
# Somente usuario logado pode acessar
@app.route('/rota1')
def rota1():
    if 'usuario_logado' not in session:
        flash('Você precisa estar logado para acessar esta página.')
        return redirect(url_for('login'))
    return render_template('salas.html')

@app.route('/rota2')
def rota2():
    if 'usuario_logado' not in session:
        flash('Você precisa estar logado para acessar esta página.')
        return redirect(url_for('login'))
    return render_template('auditorios.html')

@app.route('/rota3')
def rota3():
    if 'usuario_logado' not in session:
        flash('Você precisa estar logado para acessar esta página.')
        return redirect(url_for('login'))
    return render_template('teatros.html')

# Aqui o usuário pode fazer logout
@app.route('/logout')
def logout():
    session.pop('usuario_logado', None)
    flash('Você foi desconectado com sucesso.')
    return redirect(url_for('login'))

# Aqui o usuário pode reservar um espaço com numero dia e horario
# Verifica se  esta  disponivel aquela data e horario
# Salva no banco de dados fazeendo a ligação com o id do usuario
@app.route('/reservar/<tipo>/<int:numero>', methods=['GET', 'POST'])
def reservar_numero(tipo, numero):
    if 'usuario_logado' not in session:
        flash('Você precisa estar logado para reservar.')
        return redirect(url_for('login'))

    tipos_validos = ['sala', 'teatro', 'auditorio']
    if tipo not in tipos_validos or numero not in [1, 2, 3, 4, 5, 6]:
        flash('Tipo ou número inválido.')
        return redirect(url_for('home'))

    dias_disponiveis = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta']
    horarios_disponiveis = ['08:00', '10:00', '14:00', '16:00']

    if request.method == 'POST':
        dia = request.form['dia']
        horario = request.form['horario']

        usuario = User.query.filter_by(email_usuario=session['usuario_logado']).first()

        conflito = Reserva.query.filter_by(
            tipo_espaco=tipo,
            numero_espaco=numero,
            dia=dia,
            horario=horario
        ).first()
        if conflito:
            flash('Esse horário já está reservado. Escolha outro.')
            return redirect(url_for('reservar_numero', tipo=tipo, numero=numero))


        nova_reserva = Reserva(
            usuario_id=usuario.id_usuario,
            tipo_espaco=tipo,
            numero_espaco=numero,
            dia=dia,
            horario=horario
        )
        db.session.add(nova_reserva)
        db.session.commit()
        flash(f'{tipo.capitalize()} {numero} reservado com sucesso!')
        return render_template('reservar.html', tipo=tipo, numero=numero,
                           dias=dias_disponiveis, horarios=horarios_disponiveis)

    return render_template('reservar.html', tipo=tipo, numero=numero,
                           dias=dias_disponiveis, horarios=horarios_disponiveis)


# Aqui o usuário pode ver suas reservas
@app.route('/minhas_reservas')
def minhas_reservas():
    if 'usuario_logado' not in session:
        flash('Você precisa estar logado para ver suas reservas.')
        return redirect(url_for('login'))

    usuario = User.query.filter_by(email_usuario=session['usuario_logado']).first()
    reservas = Reserva.query.filter_by(usuario_id=usuario.id_usuario).all()

    return render_template('minhas_rese.html', reservas=reservas)


# Aqui o usuario pode cancelar suas reservas
@app.route('/cancelar_reserva/<int:id>')
def cancelar_reserva(id):
    if 'usuario_logado' not in session:
        flash('Você precisa estar logado para cancelar reservas.')
        return redirect(url_for('login'))

    reserva = Reserva.query.get_or_404(id)
    usuario = User.query.filter_by(email_usuario=session['usuario_logado']).first()

    if reserva.usuario_id != usuario.id_usuario:
        flash('Você não tem permissão para cancelar essa reserva.')
        return redirect(url_for('minhas_reservas'))

    db.session.delete(reserva)
    db.session.commit()
    flash('Reserva cancelada com sucesso.')
    return redirect(url_for('minhas_reservas'))


# Aqui permite o usuario visualizar seus dados e editar
@app.route('/meus_dados', methods=['GET', 'POST'])
def meus_dados():
    if 'usuario_logado' not in session:
        flash('Você precisa estar logado.')
        return redirect(url_for('login'))

    usuario = User.query.filter_by(email_usuario=session['usuario_logado']).first()

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        if email != usuario.email_usuario:
            email_existente = User.query.filter_by(email_usuario=email).first()
            if email_existente:
                flash('Este e-mail já está em uso por outro usuário.')
                return redirect(url_for('editar_dad'))

        usuario.nome_usuario = nome
        usuario.email_usuario = email
        usuario.senha_usuario = senha

        session['usuario_logado'] = email 
        db.session.commit()
        flash('Dados atualizados com sucesso.')
        return render_template('editar_dad.html', usuario=usuario)

    return render_template('editar_dad.html', usuario=usuario)


# Aqui o acesso é restrito ao admin 
@app.route('/painel_admin')
def painel_admin():
    if 'usuario_logado' not in session or session['usuario_logado'] != 'admin@admin.com':
        flash('Acesso restrito ao administrador.')
        return redirect(url_for('login'))

    usuarios = User.query.all() 

    return render_template('painel_admin.html', usuarios=usuarios)

# Podendo visualizar todos os usuarios cadastrados
# Deletar usuarios e reservas do mesmo
@app.route('/painel_admin/excluir_usuario/<int:id>')
def excluir_usuario(id):
    if 'usuario_logado' not in session or session['usuario_logado'] != 'admin@admin.com':
        flash('Acesso restrito ao administrador.')
        return redirect(url_for('login'))

    usuario = User.query.get_or_404(id)

    db.session.delete(usuario)
    db.session.commit()

    flash(f'Usuário {usuario.nome_usuario} e todas as reservas foram excluídos.')
    return redirect(url_for('painel_admin'))

# Excluir reservas
@app.route('/painel_admin/cancelar_reserva/<int:id>')
def cancelar_reserva_admin(id):
    if 'usuario_logado' not in session or session['usuario_logado'] != 'admin@admin.com':
        flash('Acesso restrito ao administrador.')
        return redirect(url_for('login'))

    reserva = Reserva.query.get_or_404(id)

    db.session.delete(reserva)
    db.session.commit()

    flash('Reserva cancelada com sucesso.')
    return redirect(url_for('painel_admin'))

# Aqui esta rodando a aplicação Flask no modo debug
# Isso significa que a aplicação será reiniciada automaticamente quando houver alterações no código
if __name__ == '__main__':
    app.run(debug=True)