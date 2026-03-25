from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

def conectar():
    return sqlite3.connect("database.db")

def init_db():
    conn = conectar()
    c = conn.cursor()

    c.execute("CREATE TABLE IF NOT EXISTS veiculos (placa TEXT PRIMARY KEY, nome TEXT, telefone TEXT, modelo TEXT, cor TEXT)")

    c.execute("""
    CREATE TABLE IF NOT EXISTS tipos_servico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    valor REAL
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS produtos_pneu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT
    )""")
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS servicos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    placa TEXT,
    tipo TEXT,
    valor REAL,
    entrada TEXT,
    entrega TEXT,
    origem TEXT,
    guarita TEXT,
    observacoes TEXT,
    pneu TEXT,
    cera TEXT,
    hidro_lataria TEXT,
    hidro_vidros TEXT,
    status TEXT
    )""")

    conn.commit()
    conn.close()

init_db()

@app.route("/", methods=["GET", "POST"])
def index():
    dados = None
    historico = []
    buscou = False
    placa = ""

    conn = conectar()
    c = conn.cursor()

    # 🔥 SERVIÇOS
    c.execute("SELECT * FROM tipos_servico")
    servicos_lista = c.fetchall()

    # 🔥 PNEU (SEMPRE FORA DO IF)
    c.execute("SELECT * FROM produtos_pneu")
    produtos_pneu = c.fetchall()

    if request.method == "POST":
        buscou = True
        placa = request.form.get("placa", "").upper()

        # CLIENTE
        c.execute("SELECT * FROM veiculos WHERE placa=?", (placa,))
        dados = c.fetchone()

        # HISTÓRICO
        c.execute("SELECT * FROM servicos WHERE placa=? ORDER BY id DESC", (placa,))
        historico_db = c.fetchall()

        # HISTÓRICO PREMIUM
        from datetime import datetime
        historico_formatado = []

        for s in historico_db:
            try:
                entrada = datetime.strptime(s[4], "%d/%m/%Y %H:%M")

                if s[5]:
                    entrega = datetime.strptime(s[5], "%d/%m/%Y %H:%M")
                    tempo = entrega - entrada
                    tempo_str = str(tempo)
                else:
                    tempo_str = "Em andamento"

            except:
                tempo_str = "N/A"

            historico_formatado.append((s, tempo_str))

        historico = historico_formatado

    conn.close()

    return render_template(
        "index.html",
        dados=dados,
        historico=historico,
        buscou=buscou,
        placa=placa,
        servicos_lista=servicos_lista,
        produtos_pneu=produtos_pneu
    )

@app.route("/cadastrar", methods=["POST"])
def cadastrar():
    data = request.form

    conn = conectar()
    c = conn.cursor()

    c.execute("INSERT OR IGNORE INTO veiculos VALUES (?, ?, ?, ?, ?)", (
        data["placa"].upper(),
        data["nome"],
        data["telefone"],
        data["modelo"],
        data["cor"]
    ))

    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/servico", methods=["POST"])
def servico():
    data = request.form

    from datetime import datetime
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    conn = conectar()
    c = conn.cursor()

    c.execute("""
    INSERT INTO servicos 
    (placa, tipo, valor, entrada, entrega, origem, guarita, observacoes, pneu, cera, hidro_lataria, hidro_vidros, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["placa"].upper(),
        data["tipo"],
        data["valor"],
        agora,
        "",
        data["origem"],
        data["guarita"],
        data["observacoes"],
        data["pneu"],
        data["cera"],
        data["hidro_lataria"],
        data["hidro_vidros"],
        "EM ANDAMENTO"
    ))

    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/finalizar/<int:id>")
def finalizar(id):
    from datetime import datetime
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    conn = conectar()
    c = conn.cursor()

    c.execute("UPDATE servicos SET status='FINALIZADO', entrega=? WHERE id=?", (agora, id))

    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/painel")
def painel():
    conn = conectar()
    c = conn.cursor()

    c.execute("SELECT * FROM servicos WHERE status='EM ANDAMENTO' ORDER BY id DESC")
    servicos = c.fetchall()

    conn.close()

    return render_template("painel.html", servicos=servicos)

@app.route("/cadastrar_servico", methods=["GET", "POST"])
def cadastrar_servico():
    conn = conectar()
    c = conn.cursor()

    if request.method == "POST":
        nome = request.form["nome"]
        valor = request.form["valor"]

        c.execute("INSERT INTO tipos_servico (nome, valor) VALUES (?, ?)", (nome, valor))
        conn.commit()

    c.execute("SELECT * FROM tipos_servico")
    servicos_lista = c.fetchall()

    conn.close()

    return render_template("cadastro_servico.html", servicos=servicos_lista)

@app.route("/pneu", methods=["GET", "POST"])
def cadastrar_pneu():
    conn = conectar()
    c = conn.cursor()

    if request.method == "POST":
        nome = request.form["nome"]
        c.execute("INSERT INTO produtos_pneu (nome) VALUES (?)", (nome,))
        conn.commit()

    # 🔥 LISTAR (ANTES ESTAVA FALTANDO)
    c.execute("SELECT * FROM produtos_pneu")
    lista = c.fetchall()

    conn.close()

    return render_template("pneu.html", produtos=lista)

app.run(host="0.0.0.0", port=5000)