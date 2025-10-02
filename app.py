import os
import re
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename


# -------------------------------
# Instancia do Flask
# -------------------------------
# Define o caminho da pasta 'instance' (para configs sensíveis ou DB local)
INSTANCE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance")
os.makedirs(INSTANCE_PATH, exist_ok=True)  # garante que a pasta exista

app = Flask(__name__, instance_path=INSTANCE_PATH, instance_relative_config=True)

# -------------------------------
# Configurações gerais
# -------------------------------
app.secret_key = os.environ.get("SECRET_KEY", "segredo123")

# Banco de dados (Postgres via env DATABASE_URL ou SQLite local em instance)
DB_PATH = os.path.join(INSTANCE_PATH, "entregadores.db")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Uploads
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB

# Tipos de arquivos permitidos
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

# -------------------------------
# Inicialização do banco
# -------------------------------
db = SQLAlchemy(app)

NACIONALIDADES = ["Brasileiro", "Argentino", "Chileno", "Colombiano", "Peruano", "Uruguaio", "Paraguaio", "Boliviano"]

class Entregador(db.Model):
    __tablename__ = "entregadores"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    telefone = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    tipo_chave_pix = db.Column(db.String(50), nullable=False)
    chave_pix = db.Column(db.String(150), nullable=False)
    validacao_chave_pix = db.Column(db.String(50), nullable=False)
    nacionalidade = db.Column(db.String(50), nullable=False)
    estado_civil = db.Column(db.String(50), nullable=False)
    cpf = db.Column(db.String(20), unique=True, nullable=False, index=True)
    rg = db.Column(db.String(20), nullable=False)
    data_nascimento = db.Column(db.String(20), nullable=False)
    cnpj = db.Column(db.String(20))
    cidade = db.Column(db.String(100), nullable=False)
    modal = db.Column(db.String(100), nullable=False)
    foto_rosto = db.Column(db.String(200))
    cnh = db.Column(db.String(200))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def validar_cpf(cpf: str) -> bool:
    cpf = re.sub(r"\D", "", cpf or "")
    return len(cpf) == 11

def validar_cnpj(cnpj: str | None) -> bool:
    if not cnpj:
        return True
    cnpj = re.sub(r"\D", "", cnpj)
    return len(cnpj) == 14

def padronizar_telefone(telefone: str) -> str:
    return re.sub(r"\D", "", telefone or "")

def padronizar_nome(nome: str) -> str:
    return (nome or "").strip().title()

def padronizar_email(email: str) -> str:
    return (email or "").strip().lower()

@app.route("/", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        # Foto rosto
        foto = request.files.get("foto")
        foto_filename = None
        if foto and foto.filename:
            if not _allowed_file(foto.filename):
                flash("Formato inválido para foto. Use JPG/PNG.", "error")
                return redirect(url_for("cadastro"))
            foto_filename = secure_filename(foto.filename)
            foto.save(os.path.join(app.config["UPLOAD_FOLDER"], foto_filename))

        # CNH
        cnh_file = request.files.get("cnh")
        cnh_filename = None
        if cnh_file and cnh_file.filename:
            if not _allowed_file(cnh_file.filename):
                flash("Formato inválido para CNH. Use JPG/PNG/PDF.", "error")
                return redirect(url_for("cadastro"))
            cnh_filename = secure_filename(cnh_file.filename)
            cnh_file.save(os.path.join(app.config["UPLOAD_FOLDER"], cnh_filename))

        # Campos
        nome = padronizar_nome(request.form.get("nome"))
        telefone = padronizar_telefone(request.form.get("telefone"))
        email = padronizar_email(request.form.get("email"))
        tipo_chave_pix = request.form.get("tipo_chave_pix")
        chave_pix = request.form.get("chave_pix")
        validacao_chave_pix = request.form.get("validacao_chave_pix")
        nacionalidade = request.form.get("nacionalidade")
        estado_civil = request.form.get("estado_civil")
        cpf = request.form.get("cpf")
        rg = request.form.get("rg")
        data_nascimento = request.form.get("data_nascimento")
        cnpj = request.form.get("cnpj")
        cidade = request.form.get("cidade")
        modal = request.form.get("modal")

        # Validações
        obrigatorios = { "nome": nome, "telefone": telefone, "email": email,
                         "cpf": cpf, "rg": rg, "data_nascimento": data_nascimento,
                         "cidade": cidade, "modal": modal, "tipo_chave_pix": tipo_chave_pix,
                         "chave_pix": chave_pix, "validacao_chave_pix": validacao_chave_pix,
                         "nacionalidade": nacionalidade, "estado_civil": estado_civil }
        faltando = [k for k, v in obrigatorios.items() if not v]
        if faltando:
            flash(f"Preencha os campos obrigatórios: {', '.join(faltando)}.", "error")
            return redirect(url_for("cadastro"))

        if not validar_cpf(cpf):
            flash("CPF inválido! Informe 11 dígitos.", "error")
            return redirect(url_for("cadastro"))
        if not validar_cnpj(cnpj):
            flash("CNPJ inválido! Informe 14 dígitos.", "error")
            return redirect(url_for("cadastro"))

        # Persistência
        novo = Entregador(nome=nome, telefone=telefone, email=email,
                          tipo_chave_pix=tipo_chave_pix, chave_pix=chave_pix,
                          validacao_chave_pix=validacao_chave_pix, nacionalidade=nacionalidade,
                          estado_civil=estado_civil, cpf=cpf, rg=rg,
                          data_nascimento=data_nascimento, cnpj=cnpj,
                          cidade=cidade, modal=modal, foto_rosto=foto_filename,
                          cnh=cnh_filename)
        try:
            db.session.add(novo)
            db.session.commit()
            flash("Cadastro realizado com sucesso!", "success")
            return redirect(url_for("cadastro"))
        except IntegrityError:
            db.session.rollback()
            flash("CPF já cadastrado.", "error")
            return redirect(url_for("cadastro"))

    return render_template("formulario.html", nacionalidades=NACIONALIDADES)

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=False)

@app.route("/dashboard")
def dashboard():
    entregadores = Entregador.query.all()
    total_entregadores = len(entregadores)
    total_cidades = len({e.cidade for e in entregadores})
    total_modal_moto = sum(1 for e in entregadores if e.modal.lower() == "moto")
    total_modal_bicicleta = sum(1 for e in entregadores if e.modal.lower() == "bicicleta")
    nacionalidades_count = {}
    estado_civil_count = {}
    tipos_chave_pix_count = {}
    cidades_count = {}
    modais_count = {}
    for e in entregadores:
        nacionalidades_count[e.nacionalidade] = nacionalidades_count.get(e.nacionalidade, 0) + 1
        estado_civil_count[e.estado_civil] = estado_civil_count.get(e.estado_civil, 0) + 1
        tipos_chave_pix_count[e.tipo_chave_pix] = tipos_chave_pix_count.get(e.tipo_chave_pix, 0) + 1
        cidades_count[e.cidade] = cidades_count.get(e.cidade, 0) + 1
        modais_count[e.modal] = modais_count.get(e.modal, 0) + 1
    return render_template("dashboard.html", entregadores=entregadores,
                           total_entregadores=total_entregadores,
                           total_cidades=total_cidades,
                           total_modal_moto=total_modal_moto,
                           total_modal_bicicleta=total_modal_bicicleta,
                           nacionalidades_count=nacionalidades_count,
                           estado_civil_count=estado_civil_count,
                           tipos_chave_pix_count=tipos_chave_pix_count,
                           cidades_count=cidades_count,
                           modais_count=modais_count)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
