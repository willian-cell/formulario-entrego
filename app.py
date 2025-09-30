import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask import send_from_directory


app = Flask(__name__)
app.secret_key = "segredo123"

# Configuração do banco de dados: 
# Se estiver no ambiente de produção, usa o MySQL, caso contrário, usa o SQLite
if os.environ.get('DATABASE_URL'):
    # Para produção no PythonAnywhere (ou outra nuvem com MySQL)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
else:
    # Para desenvolvimento local com SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///entregadores.db'

# Configurações de Upload
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)

# Garante que a pasta de uploads existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Inicializando o banco de dados
# O restante da c


# ==========================
# Lista de Nacionalidades
# ==========================
NACIONALIDADES = [
    "Brasileiro",
    "Argentino",
    "Chileno",
    "Colombiano",
    "Peruano",
    "Uruguaio",
    "Paraguaio",
    "Boliviano",
    "Equatoriano",
    "Venezuelano",
    "Mexicano",
    "Cubano",
    "Dominicano",
    "Guatemalteco",
    "Hondurenho",
    "Salvadorenho",
    "Nicaraguense",
    "Costa-riquenho",
    "Panamenho",
    "Porto-riquenho"
]

# ==========================
# Modelo do Banco
# ==========================
class Entregador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    telefone = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    tipo_chave_pix = db.Column(db.String(50), nullable=False)
    chave_pix = db.Column(db.String(150), nullable=False)
    validacao_chave_pix = db.Column(db.String(50), nullable=False)
    nacionalidade = db.Column(db.String(50), nullable=False)
    estado_civil = db.Column(db.String(50), nullable=False)
    cpf = db.Column(db.String(20), unique=True, nullable=False)
    rg = db.Column(db.String(20), nullable=False)
    data_nascimento = db.Column(db.String(20), nullable=False)
    cnpj = db.Column(db.String(20))
    cidade = db.Column(db.String(100), nullable=False)
    modal = db.Column(db.String(100), nullable=False)
    foto_rosto = db.Column(db.String(200))

# ==========================
# Rota Principal
# ==========================
@app.route("/", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        foto = request.files.get("foto")
        filename = None

        if foto and foto.filename != "":
            filename = secure_filename(foto.filename)
            foto.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        novo = Entregador(
            nome=request.form["nome"],
            telefone=request.form["telefone"],
            email=request.form["email"],
            tipo_chave_pix=request.form["tipo_chave_pix"],
            chave_pix=request.form["chave_pix"],
            validacao_chave_pix=request.form["validacao_chave_pix"],
            nacionalidade=request.form["nacionalidade"],  # recebe do select
            estado_civil=request.form["estado_civil"],
            cpf=request.form["cpf"],
            rg=request.form["rg"],
            data_nascimento=request.form["data_nascimento"],
            cnpj=request.form["cnpj"],
            cidade=request.form["cidade"],
            modal=request.form["modal"],
            foto_rosto=filename
        )
        db.session.add(novo)
        db.session.commit()
        flash("Cadastro realizado com sucesso!", "success")
        return redirect(url_for("cadastro"))

    return render_template("formulario.html", nacionalidades=NACIONALIDADES)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/dashboard")
def dashboard():
    entregadores = Entregador.query.all()  # busca todos do banco

    # Contadores gerais
    total_entregadores = len(entregadores)
    total_cidades = len(set([e.cidade for e in entregadores]))
    total_modal_moto = len([e for e in entregadores if e.modal == "Moto"])
    total_modal_bicicleta = len([e for e in entregadores if e.modal == "Bicicleta"])

    # Análise de nacionalidade
    nacionalidades_count = {}
    for e in entregadores:
        if e.nacionalidade not in nacionalidades_count:
            nacionalidades_count[e.nacionalidade] = 1
        else:
            nacionalidades_count[e.nacionalidade] += 1

    # Análise de estado civil
    estado_civil_count = {}
    for e in entregadores:
        if e.estado_civil not in estado_civil_count:
            estado_civil_count[e.estado_civil] = 1
        else:
            estado_civil_count[e.estado_civil] += 1

    # Análise de tipos de chave PIX
    tipos_chave_pix_count = {}
    for e in entregadores:
        if e.tipo_chave_pix not in tipos_chave_pix_count:
            tipos_chave_pix_count[e.tipo_chave_pix] = 1
        else:
            tipos_chave_pix_count[e.tipo_chave_pix] += 1

    # Análise de cidades
    cidades_count = {}
    for e in entregadores:
        if e.cidade not in cidades_count:
            cidades_count[e.cidade] = 1
        else:
            cidades_count[e.cidade] += 1

    # Contador de todos os tipos de modal
    modais_count = {}
    for e in entregadores:
        if e.modal not in modais_count:
            modais_count[e.modal] = 1
        else:
            modais_count[e.modal] += 1


    return render_template("dashboard.html", 
                           entregadores=entregadores,
                           total_entregadores=total_entregadores,
                           total_cidades=total_cidades,
                           total_modal_moto=total_modal_moto,
                           total_modal_bicicleta=total_modal_bicicleta,
                           nacionalidades_count=nacionalidades_count,
                           estado_civil_count=estado_civil_count,
                           tipos_chave_pix_count=tipos_chave_pix_count,
                           cidades_count=cidades_count,
                           modais_count=modais_count)

# ==========================
# Inicialização
# ==========================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
