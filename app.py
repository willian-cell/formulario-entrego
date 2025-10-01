import os
import re
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for, flash, send_from_directory
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

# ---------------------
# Configuração básica
# ---------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "segredo123")

# DB: Render normalmente fornece DATABASE_URL (Postgres). Local: SQLite.
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    # Render às vezes fornece URL em formato antigo; SQLAlchemy 2 aceita ambos.
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///entregadores.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Uploads
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Limite global (Flask rejeita requests maiores automaticamente)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

db = SQLAlchemy(app)

# ---------------------
# Constantes
# ---------------------
NACIONALIDADES = [
    "Brasileiro", "Argentino", "Chileno", "Colombiano", "Peruano",
    "Uruguaio", "Paraguaio", "Boliviano", "Equatoriano", "Venezuelano",
    "Mexicano", "Cubano", "Dominicano", "Guatemalteco", "Hondurenho",
    "Salvadorenho", "Nicaraguense", "Costa-riquenho", "Panamenho",
    "Porto-riquenho"
]

# ---------------------
# Modelo
# ---------------------
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
    data_nascimento = db.Column(db.String(20), nullable=False)  # manter string p/ compatibilidade do form
    cnpj = db.Column(db.String(20))
    cidade = db.Column(db.String(100), nullable=False)
    modal = db.Column(db.String(100), nullable=False)
    foto_rosto = db.Column(db.String(200))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

# ---------------------
# Helpers de validação
# ---------------------
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

# ---------------------
# Rotas
# ---------------------
@app.route("/", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        # ----------------- Upload da foto (opcional) -----------------
        foto = request.files.get("foto")
        filename = None

        if foto and foto.filename:
            if not _allowed_file(foto.filename):
                flash("Formato de imagem inválido. Use JPG ou PNG.", "error")
                return redirect(url_for("cadastro"))

            # medir tamanho com stream (além do MAX_CONTENT_LENGTH)
            foto.stream.seek(0, os.SEEK_END)
            size = foto.stream.tell()
            foto.stream.seek(0)
            if size > 5 * 1024 * 1024:
                flash("A foto não pode ultrapassar 5MB.", "error")
                return redirect(url_for("cadastro"))

            filename = secure_filename(foto.filename)
            caminho = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            foto.save(caminho)

        # ----------------- Campos do formulário -----------------
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

        # ----------------- Validações mínimas -----------------
        obrigatorios = {
            "nome": nome, "telefone": telefone, "email": email, "cpf": cpf, "rg": rg,
            "data_nascimento": data_nascimento, "cidade": cidade, "modal": modal,
            "tipo_chave_pix": tipo_chave_pix, "chave_pix": chave_pix,
            "validacao_chave_pix": validacao_chave_pix, "nacionalidade": nacionalidade,
            "estado_civil": estado_civil
        }
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

        # ----------------- Persistência -----------------
        novo = Entregador(
            nome=nome,
            telefone=telefone,
            email=email,
            tipo_chave_pix=tipo_chave_pix,
            chave_pix=chave_pix,
            validacao_chave_pix=validacao_chave_pix,
            nacionalidade=nacionalidade,
            estado_civil=estado_civil,
            cpf=cpf,
            rg=rg,
            data_nascimento=data_nascimento,
            cnpj=cnpj,
            cidade=cidade,
            modal=modal,
            foto_rosto=filename
        )

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

    return render_template(
        "dashboard.html",
        entregadores=entregadores,
        total_entregadores=total_entregadores,
        total_cidades=total_cidades,
        total_modal_moto=total_modal_moto,
        total_modal_bicicleta=total_modal_bicicleta,
        nacionalidades_count=nacionalidades_count,
        estado_civil_count=estado_civil_count,
        tipos_chave_pix_count=tipos_chave_pix_count,
        cidades_count=cidades_count,
        modais_count=modais_count
    )

@app.route("/health")
def health():
    # Útil para checagens do Render
    return {"status": "ok"}, 200

# ---------------------
# Inicialização
# ---------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    # Em produção, o gunicorn vai iniciar; debug só local.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
