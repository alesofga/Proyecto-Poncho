import sqlite3
from faker import Faker
import random
from datetime import date, datetime
import uuid
from flask import Flask, request, redirect, render_template_string, session, url_for, flash, jsonify
import pywhatkit as kit
import os
import base64
import json
import requests
from flask_mail import Mail, Message
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

DB_NAME = 'mexico_sinsordera.db'

CREATE_TABLES = [
    ("Usuario",
     """
     CREATE TABLE IF NOT EXISTS Usuario (
         id TEXT PRIMARY KEY,
         nombre TEXT,
         correo TEXT,
         usuario TEXT,
         contraseña TEXT,
         numero_empleado TEXT,
         stars INTEGER
     )"""),
    ("Bitacora",
     """
     CREATE TABLE IF NOT EXISTS Bitacora (
         idbitacora INTEGER PRIMARY KEY,
         timestamp TEXT,
         fechallamada TEXT,
         obs TEXT
     )"""),
    ("Agenda",
     """
     CREATE TABLE IF NOT EXISTS Agenda (
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         nombre TEXT,
         phone TEXT,
         img TEXT
     )"""),
    ("Padres",
     """
     CREATE TABLE IF NOT EXISTS Padres (
         id TEXT,
         nombre_candidato TEXT,
         nombre_padre TEXT,
         nombre_madre TEXT,
         escolaridad_padre TEXT,
         escolaridad_madre TEXT,
         ocupacion_padre TEXT,
         ocupacion_madre TEXT,
         lugar_trabajo_padre TEXT,
         lugar_trabajo_madre TEXT,
         estado_civil_padre TEXT,
         estado_civil_madre TEXT,
         PRIMARY KEY(id, nombre_candidato)
     )"""),
    ("Diagnostico",
     """
     CREATE TABLE IF NOT EXISTS Diagnostico (
         id TEXT,
         nombre_candidato TEXT,
         nombre_doctor TEXT,
         medico_especialista TEXT,
         PRIMARY KEY(id, nombre_candidato)
     )"""),
    ("Implante",
     """
     CREATE TABLE IF NOT EXISTS Implante (
         id TEXT,
         nombre_candidato TEXT,
         utiliza_implante TEXT,
         marca TEXT,
         modelo TEXT,
         conoce_causa TEXT,
         causa TEXT,
         PRIMARY KEY(id, nombre_candidato)
     )"""),
    ("Beneficiario",
     """
     CREATE TABLE IF NOT EXISTS Beneficiario (
         id TEXT,
         nombre_paciente TEXT,
         fecha_nacimiento TEXT,
         lugar_nacimiento TEXT,
         edad INTEGER,
         sexo TEXT,
         escolaridad TEXT,
         ocupacion TEXT,
         curp TEXT,
         numero_seguridad_social TEXT,
         afiliacion TEXT,
         cuenta_seguro TEXT,
         compania_seguro TEXT,
         estudio_socio TEXT,
         rango TEXT,
         servicio TEXT,
         PRIMARY KEY(id, nombre_paciente)
     )"""),
    ("Responsable",
     """
     CREATE TABLE IF NOT EXISTS Responsable (
         id TEXT,
         nombre_paciente TEXT,
         nombre_responsable TEXT,
         parentesco TEXT,
         seguro_social TEXT,
         numero_seguridad_social TEXT,
         correo TEXT,
         celular TEXT,
         PRIMARY KEY(id, nombre_paciente)
     )"""),
    ("Rehabilitacion",
     """
     CREATE TABLE IF NOT EXISTS Rehabilitacion (
         id TEXT,
         nombre_terapeuta TEXT,
         tipo_terapia TEXT,
         edad_auditiva INTEGER,
         comunica TEXT,
         PRIMARY KEY(id, nombre_terapeuta)
     )"""),
    ("Referencias",
     """
     CREATE TABLE IF NOT EXISTS Referencias (
         id TEXT PRIMARY KEY,
         medio_conocer TEXT,
         red_social TEXT,
         referencia TEXT
     )"""),
    ("Cirugia",
     """
     CREATE TABLE IF NOT EXISTS Cirugia (
         id TEXT,
         numero_candidato TEXT,
         electrodo TEXT,
         configuracion TEXT,
         tipo_implante TEXT,
         medico_encendido TEXT,
         fecha_encendido TEXT,
         mapeos TEXT,
         PRIMARY KEY(id, numero_candidato)
     )"""),
    ("Paciente",
     """
     CREATE TABLE IF NOT EXISTS Paciente (
         id TEXT,
         nombre_candidato TEXT,
         expediente TEXT,
         firmo_formulario TEXT,
         hospital TEXT,
         estado TEXT,
         municipio TEXT,
         nombre_cirujano TEXT,
         nombre_terapeuta TEXT,
         nombre_audiologo TEXT,
         centro_implante TEXT,
         ayuda_auditiva TEXT,
         PRIMARY KEY(id, nombre_candidato)
     )"""),
    ("Donantes",
     """
     CREATE TABLE IF NOT EXISTS Donantes (
         id TEXT,
         tipo_donante TEXT,
         sector_donante TEXT,
         nombre_donante TEXT,
         telefono_donante TEXT,
         correo_donante TEXT,
         direccion_donante TEXT,
         redes_sociales TEXT,
         observaciones_donante TEXT
     )"""),
    ("Historial",
     """
     CREATE TABLE IF NOT EXISTS Historial (
         id TEXT PRIMARY KEY,
         nombre TEXT,
         numero TEXT,
         fecha_registro TEXT
     )""")
]

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    for _, ddl in CREATE_TABLES:
        c.execute(ddl)
    conn.commit()
    return conn

def create_and_populate(n_users=20, n_records=10):
    fake = Faker('es_MX')
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    for _, ddl in CREATE_TABLES:
        c.execute(ddl)
    conn.commit()
    conn.commit()
    conn.close()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key")

app.config.update(
    MAIL_SERVER         = 'smtp.gmail.com',
    MAIL_PORT           = 587,
    MAIL_USE_TLS        = True,
    MAIL_USE_SSL        = False,
    MAIL_USERNAME       = 'gerardowisselberg@gmail.com',
    MAIL_PASSWORD       = 'hxtw wfem fxaj bfit',
    MAIL_DEFAULT_SENDER = ('México Sin Sordera AC','noreply@mexicosinsordera.org.mx')
)
mail = Mail(app)

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID","")
TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN","")
TWILIO_PHONE_NUMBER= os.getenv("TWILIO_PHONE_NUMBER","")

def format_phone(phone: str) -> str:
    cleaned = "".join(ch for ch in phone if ch.isdigit())
    if not cleaned.startswith("52"):
        cleaned = "52"+cleaned
    return f"+{cleaned}"

@app.route("/autocomplete_email")
def autocomplete_email():
    q = request.args.get("q","").strip()
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT nombre, correo FROM Usuario WHERE nombre LIKE ? OR correo LIKE ? LIMIT 5",
                (f"%{q}%", f"%{q}%"))
    results = cur.fetchall(); conn.close()
    return jsonify([{"label": f"{r['nombre']} <{r['correo']}>", "value": r['correo']} for r in results])

@app.route("/")
def landing():
    return render_template_string("""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><title>Bienvenido</title>
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>body{font-family:Arial,sans-serif;background:#f5f5f5;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}
.container{text-align:center;background:#fff;padding:40px;border-radius:8px;box-shadow:0 0 10px rgba(0,0,0,0.1)}
a{display:inline-block;margin:10px;padding:10px 20px;background:#2ebf91;color:#fff;text-decoration:none;border-radius:4px}
a:hover{background:#28a17b}</style></head>
<body><div class="container">
  <h1>Bienvenido a México Sin Sordera AC</h1><p>Por favor, inicia sesión o regístrate.</p>
  <a href="/login">Login</a><a href="/register">Registro</a>
</div></body></html>""")

@app.route("/login", methods=["GET","POST"])
def login_page():
    if request.method=="POST":
        u = request.form["usuario"]; p = request.form["contraseña"]
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT * FROM Usuario WHERE usuario=? AND contraseña=?", (u,p))
        user = cur.fetchone(); conn.close()
        if user:
            session["user_id"]=user["id"]; flash("Login exitoso"); return redirect(url_for("dashboard"))
        flash("Credenciales incorrectas"); return redirect(url_for("login_page"))
    return render_template_string("""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Login</title><meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>body{font-family:Arial;background:#f5f5f5;padding:20px}.form-container{max-width:400px;margin:50px auto;background:#fff;padding:20px;border-radius:4px;box-shadow:0 0 10px rgba(0,0,0,0.1)}
h2{text-align:center;color:#2ebf91;margin-bottom:20px}.form-group{margin-bottom:15px}.form-group label{display:block;margin-bottom:5px;color:#333}.form-group input{width:100%;padding:8px;border:1px solid #ccc;border-radius:4px}
.btn{width:100%;background:#2ebf91;color:#fff;padding:10px;border:none;border-radius:4px;cursor:pointer}.btn:hover{background:#28a17b}
.link{text-align:center;margin-top:15px}.link a{color:#2ebf91;text-decoration:none}.link a:hover{text-decoration:underline}
</style></head><body><div class="form-container"><h2>Login</h2>
<form method="POST"><div class="form-group"><label>Usuario</label><input type="text" name="usuario" required></div>
<div class="form-group"><label>Contraseña</label><input type="password" name="contraseña" required></div>
<button type="submit" class="btn">Iniciar Sesión</button></form>
<div class="link"><p>¿No tienes cuenta? <a href="/register">Regístrate</a></p></div></div></body></html>""")

@app.route("/register", methods=["GET","POST"])
def register_page():
    if request.method=="POST":
        nombre=request.form["nombre"]; correo=request.form["correo"]
        usuario=request.form["usuario"]; pwd=request.form["contraseña"]
        cpwd=request.form["confirmar_contraseña"]; tel=request.form["numero_empleado"]
        if pwd!=cpwd: flash("Las contraseñas no coinciden"); return redirect(url_for("register_page"))
        uid=str(uuid.uuid4()); conn=get_db_connection(); cur=conn.cursor()
        cur.execute("INSERT INTO Usuario VALUES(?,?,?,?,?,?,?)",(uid,nombre,correo,usuario,pwd,tel,0))
        cur.execute("INSERT INTO Historial VALUES(?,?,?,?)",(uid,nombre,tel,date.today().isoformat()))
        conn.commit(); conn.close(); flash("Registro exitoso, por favor inicia sesión"); return redirect(url_for("login_page"))
    return render_template_string("""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Registro</title><meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>body{font-family:Arial;background:#f5f5f5;padding:20px}.form-container{max-width:400px;margin:50px auto;background:#fff;padding:20px;border-radius:4px;box-shadow:0 0 10px rgba(0,0,0,0.1)}
h2{text-align:center;color:#2ebf91;margin-bottom:20px}.form-group{margin-bottom:15px}.form-group label{display:block;margin-bottom:5px;color:#333}.form-group input{width:100%;padding:8px;border:1px solid #ccc;border-radius:4px}
.btn{width:100%;background:#2ebf91;color:#fff;padding:10px;border:none;border-radius:4px;cursor:pointer}.btn:hover{background:#28a17b}
.link{text-align:center;margin-top:15px}.link a{color:#2ebf91;text-decoration:none}.link a:hover{text-decoration:underline}
</style></head><body><div class="form-container"><h2>Registro</h2>
<form method="POST"><div class="form-group"><label>Nombre</label><input type="text" name="nombre" required></div>
<div class="form-group"><label>Correo</label><input type="email" name="correo" required></div>
<div class="form-group"><label>Usuario</label><input type="text" name="usuario" required></div>
<div class="form-group"><label>Contraseña</label><input type="password" name="contraseña" required></div>
<div class="form-group"><label>Confirmar Contraseña</label><input type="password" name="confirmar_contraseña" required></div>
<div class="form-group"><label>Teléfono</label><input type="text" name="numero_empleado" placeholder="5511864680"></div>
<button type="submit" class="btn">Registrarse</button></form>
<div class="link"><p>¿Ya tienes cuenta? <a href="/login">Inicia sesión</a></p></div></div></body></html>""")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session: return redirect(url_for("login_page"))
    q = request.args.get("q","").strip()
    conn=get_db_connection(); cur=conn.cursor()
    if q:
        cur.execute("SELECT id,nombre,stars,numero_empleado FROM Usuario WHERE nombre LIKE ? OR numero_empleado LIKE ?",
                    (f"%{q}%",f"%{q}%"))
    else:
        cur.execute("SELECT id,nombre,stars,numero_empleado FROM Usuario")
    contactos=cur.fetchall()
    contactos_html=""
    for c in contactos:
        stars_html="".join('<i class="fa-solid fa-star"></i>' if i<c["stars"] else '<i class="fa-regular fa-star"></i>' for i in range(5))
        phone_fmt=format_phone(c["numero_empleado"]) if c["numero_empleado"] else ""
        contactos_html+=f"""
        <div class="contact-row">
          <div class="contact-info">
            <i class="fa-solid fa-user-circle contact-icon"></i>
            <div><div class="contact-phone">{phone_fmt}</div><div class="contact-name">{c['nombre']}</div></div>
          </div>
          <div class="contact-stars">{stars_html}</div>
          <div class="contact-actions">
            <a href="/editar_contacto/{c['id']}"><i class="fa-solid fa-pen"></i></a>
            <a href="/eliminar_contacto/{c['id']}" onclick="return confirm('¿Estás seguro?')"><i class="fa-solid fa-trash-can"></i></a>
            <a href="/whatsapp_mensaje/{c['id']}"><i class="fa-brands fa-whatsapp"></i></a>
            <a href="/llamar/{c['id']}"><i class="fa-solid fa-phone"></i></a>
          </div>
        </div>"""
    # bitácora
    cur.execute("SELECT idbitacora,timestamp,fechallamada,obs FROM Bitacora")
    bitacora_rows="".join(f"<tr><td>{b['idbitacora']}</td><td>{b['timestamp']}</td><td>{b['fechallamada']}</td><td>{b['obs']}</td></tr>" for b in cur.fetchall())
    # beneficiarios
    cur.execute("""
        SELECT b.*,p.nombre_padre,p.nombre_madre
        FROM Beneficiario b
        LEFT JOIN Padres p ON b.id=p.id AND b.nombre_paciente=p.nombre_candidato
    """)
    agenda_html=""
    for r in cur.fetchall():
        edad=int(r['edad'] or 0)
        padres=""
        if edad<18:
            padres=f"<div class='padres-info'><h4>Padres</h4><p><strong>Padre:</strong> {r['nombre_padre'] or '—'}</p><p><strong>Madre:</strong> {r['nombre_madre'] or '—'}</p></div>"
        agenda_html+=f"""
        <div class="beneficiario-card">
          <h3>{r['nombre_paciente']}</h3>
          <p><strong>Nac.:</strong> {r['fecha_nacimiento']} en {r['lugar_nacimiento']}</p>
          <p><strong>Edad:</strong> {edad}</p>
          {padres}
        </div>"""
    # información
    informacion_html="""
    <div class="info-card">
      <h2>Información de la Asociación</h2>
      <p><strong>México Sin Sordera AC</strong> apoya a personas con pérdida auditiva.</p>
      <a href="https://mexicosinsordera.org.mx/" target="_blank">Nuestro sitio oficial</a>
      <div class="map-wrapper">
        <iframe
  width="100%" height="300"
  frameborder="0" style="border:0"
  src="https://maps.google.com/maps?q=Mexico%20Sin%20Sordera%20AC&output=embed"
  allowfullscreen>
</iframe>
      </div>
    </div>"""
    # donantes
    cur.execute("SELECT * FROM Donantes")
    donantes_html=""
    for d in cur.fetchall():
        donantes_html+=f"""
        <div class="donante-card">
          <h3>{d['nombre_donante']}</h3>
          <p><strong>Tipo:</strong> {d['tipo_donante']}</p>
          <p><strong>Teléfono:</strong> {d['telefono_donante']}</p>
          <p><strong>Correo:</strong> {d['correo_donante']}</p>
        </div>"""
    conn.close()

    # sección correo + autocomplete
    email_section_html = """
    <h2>Enviar correo</h2>

    <form action="/send_email" method="POST" class="correo-form" autocomplete="off" enctype="multipart/form-data">
      <div class="form-group"><label>De</label><input type="email" name="from_email" required></div>
      <div class="form-group"><label>Para</label>
        <input type="text" id="to_input" name="to_list" placeholder="Escribe nombre..." required>
        <ul id="suggestions" class="suggestions-list"></ul>
      </div>
      <div class="form-group"><label>Asunto</label><input type="text" name="subject" required></div>
      <div class="form-group"><label>Mensaje</label><textarea name="body" style="height:150px;" required></textarea></div>
      <div class="form-group">
        <label>Adjuntos</label>
        <input type="file" name="adjuntos" multiple>
        </div>
      <button type="submit" class="save-button">Enviar correo</button>
    </form>
    <style>
      .correo-form{border:1px solid #eee;padding:15px;margin-bottom:10px;border-radius:8px;background:#fff}
      .correo-form .form-group{margin-bottom:10px}
      .correo-form .form-group label{display:block;margin-bottom:5px;color:#333}
      .correo-form .form-group input,
      .correo-form .form-group textarea{width:100%;padding:8px;border:1px solid #ccc;border-radius:4px}
      .suggestions-list{position:absolute;top:100%;left:0;right:0;border:1px solid #ccc;background:#fff;z-index:1000;max-height:120px;overflow-y:auto;list-style:none;margin:0;padding:0}
      .suggestions-list li{padding:8px;cursor:pointer}
      .suggestions-list li:hover{background:#f0f0f0}
    </style>
    <script>
      const toInput=document.getElementById('to_input'),
            suggestions=document.getElementById('suggestions');
      toInput.addEventListener('input',async()=>{
        let q=toInput.value.trim(); if(!q){suggestions.innerHTML='';return;}
        let res=await fetch(/autocomplete_email?q=${encodeURIComponent(q)});
        let items=await res.json();
        suggestions.innerHTML=items.map(it=><li data-value="${it.value}">${it.label}</li>).join('');
      });
      suggestions.addEventListener('click',e=>{if(e.target.tagName==='LI'){
        toInput.value=e.target.dataset.value; suggestions.innerHTML='';
      }});
      document.addEventListener('click',e=>{if(!toInput.contains(e.target)&&!suggestions.contains(e.target))
        suggestions.innerHTML='';
      });
    </script>
    """

    return render_template_string("""
<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>México Sin Sordera AC</title>
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Arial,sans-serif;background:#f5f5f5;color:#333}
.side-nav{width:60px;background:#fff;border-right:1px solid #ddd;display:flex;flex-direction:column;align-items:center;padding-top:10px}
.nav-icon{width:40px;height:40px;border-radius:50%;margin:10px 0;display:flex;align-items:center;justify-content:center;cursor:pointer;color:#666}
.nav-icon:hover{background:#f0f0f0;color:#333}
.nav-icon.active{background:#2ebf91;color:#fff}
.app-container{display:flex;height:100vh;width:100vw}
.main-content{flex:1;display:flex;flex-direction:column}
.header{background:#fff;display:flex;align-items:center;padding:0 20px;height:60px;border-bottom:1px solid #ddd}
.logo-area{display:flex;align-items:center;margin-right:20px}
.logo-img{height:40px;margin-right:10px}
.logo-text{font-weight:bold;font-size:1.2em;color:#2ebf91}
.search-bar{flex:1;position:relative;max-width:400px}
.search-bar input{width:100%;padding:8px 35px 8px 10px;border-radius:4px;border:1px solid #ccc}
.search-bar i{position:absolute;right:10px;top:50%;transform:translateY(-50%);color:#aaa}
.add-button{background:#2ebf91;color:#fff;border:none;padding:8px 20px;border-radius:4px;cursor:pointer;margin-left:20px}
.add-button:hover{background:#28a17b}
.content-sections{flex:1;overflow:auto;padding:10px 20px;background:#fff}
.section{display:none}
.section.active{display:block}
.contact-row{display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f0f0f0}
.contact-info{display:flex;align-items:center;gap:10px}
.contact-icon{font-size:1.8em;color:#2ebf91}
.contact-phone{font-weight:600;font-size:0.9em;color:#555}
.contact-name{font-size:0.8em;color:#999}
.contact-stars i{color:#FFD700;margin-right:2px}
.contact-actions a,.contact-actions i{margin-left:10px;color:#888;cursor:pointer;text-decoration:none}
.contact-actions a:hover,.contact-actions i:hover{color:#333}
.bitacora-table{width:100%;border-collapse:collapse;margin-top:10px}
.bitacora-table th,.bitacora-table td{border:1px solid #eee;padding:8px;font-size:0.9em}
.bitacora-table th{background:#fafafa;text-align:left;color:#666}
.beneficiario-card,.donante-card,.info-card{border:1px solid #eee;padding:15px;margin-bottom:10px;border-radius:8px;background:#fff}
.padres-info{margin-top:10px;padding:10px;background:#f9f9f9;border-radius:6px}
.save-button{background:#2ebf91;color:#fff;border:none;padding:8px 15px;border-radius:4px;cursor:pointer}
.save-button:hover{background:#28a17b}
.form-container{position:fixed;top:0;right:-100%;width:30%;max-width:500px;height:100%;background:#fff;box-shadow:-2px 0 10px rgba(0,0,0,0.2);transition:right .3s ease;overflow-y:auto;z-index:9999}
.form-container.show{right:0}
.form-header{display:flex;justify-content:space-between;align-items:center;padding:15px;border-bottom:1px solid #ddd}
.form-header h3{margin:0;font-size:1.2em;color:#2ebf91}
.close-btn{background:#f44336;color:#fff;border:none;border-radius:4px;padding:5px 10px;cursor:pointer}
.close-btn:hover{background:#d73225}
.form-body{padding:15px}
.tab-buttons{display:flex;gap:5px;margin-bottom:10px}
.tab-button{flex:1;padding:8px;border:none;background:#eee;cursor:pointer;border-radius:4px;font-size:0.9em;color:#666}
.tab-button.active{background:#2ebf91;color:#fff}
.tab-panel{display:none}
.tab-panel.active{display:block}
.form-group{margin-bottom:10px}
.form-group label{display:block;margin-bottom:5px;color:#333}
.form-group input,.form-group select,.form-group textarea{width:100%;padding:8px;border:1px solid #ccc;border-radius:4px}
.save-container{text-align:right;margin:15px}
</style>
<script>
function selectNav(i){
  const icons=document.querySelectorAll('.nav-icon'),
        secs=document.querySelectorAll('.section');
  icons.forEach(ic=>ic.classList.remove('active'));
  icons[i].classList.add('active');
  secs.forEach(s=>s.classList.remove('active'));
  secs[i].classList.add('active');
}
function openForm(){document.getElementById('form-container').classList.add('show')}
function closeForm(){document.getElementById('form-container').classList.remove('show')}
function showTab(i){
  const ps=document.querySelectorAll('.tab-panel'),
        bs=document.querySelectorAll('.tab-button');
  ps.forEach((p,j)=>{p.classList.remove('active');bs[j].classList.remove('active')});
  ps[i].classList.add('active');bs[i].classList.add('active');
}
</script>
</head><body>
<div class="app-container">
  <div class="side-nav">
    <div class="nav-icon active" onclick="selectNav(0)"><i class="fa-solid fa-address-book"></i></div>
    <div class="nav-icon" onclick="selectNav(1)"><i class="fa-solid fa-phone"></i></div>
    <div class="nav-icon" onclick="selectNav(2)"><i class="fa-solid fa-calendar"></i></div>
    <div class="nav-icon" onclick="selectNav(3)"><i class="fa-solid fa-circle-info"></i></div>
    <div class="nav-icon" onclick="selectNav(4)"><i class="fa-solid fa-table-cells"></i></div>
    <div class="nav-icon" onclick="selectNav(5)"><i class="fa-solid fa-envelope"></i></div>
  </div>
  <div class="main-content">
    <div class="header">
      <div class="logo-area">
        <img src="/static/images/logo.jpeg" alt="Logo" class="logo-img">
        <div class="logo-text">México Sin Sordera AC</div>
      </div>
      <div class="search-bar">
        <form action="/dashboard" method="GET">
          <input type="text" name="q" placeholder="Buscar..." value="{{ q }}">
          <i class="fa-solid fa-magnifying-glass"></i>
        </form>
      </div>
      <button class="add-button" onclick="openForm()">
        <i class="fa-solid fa-plus"></i> Add
      </button>
    </div>
    <div class="content-sections">
      <div class="section active"><h2>Contactos</h2>{{ contactos_html|safe }}</div>
      <div class="section"><h2>Bitácora</h2><table class="bitacora-table"><thead><tr><th>ID</th><th>Timestamp</th><th>Fecha Llamada</th><th>Obs</th></tr></thead><tbody>{{ bitacora_rows|safe }}</tbody></table></div>
      <div class="section"><h2>Beneficiarios</h2>{{ agenda_html|safe }}</div>
      <div class="section">{{ informacion_html|safe }}</div>
      <div class="section">{{ donantes_html|safe }}</div>
      <div class="section">{{ email_section_html|safe }}</div>
    </div>
  </div>
</div>

<div id="form-container" class="form-container">
  <div class="form-header">
    <h3>Formulario Contacto</h3>
    <button class="close-btn" onclick="closeForm()">X</button>
  </div>
  <form action="/guardar_contacto" method="POST">
    <div class="form-body">
      <div class="tab-buttons">
        <button type="button" class="tab-button active" onclick="showTab(0)">Datos Generales</button>
        <button type="button" class="tab-button" onclick="showTab(1)">Beneficiarios y Patrones</button>
        <button type="button" class="tab-button" onclick="showTab(2)">Datos Médicos</button>
        <button type="button" class="tab-button" onclick="showTab(3)">Rehabilitación</button>
      </div>
      <!-- TAB 0 -->
      <div class="tab-panel active">
        <div class="form-group"><label>Email</label><input type="email" name="email" placeholder="correo@ejemplo.com"></div>
        <div class="form-group"><label>IDContacto</label><input type="text" name="idcontacto" placeholder="Ej: 127-43-F4++"></div>
        <div class="form-group"><label>Usuario</label><input type="text" name="usuario" placeholder="Nombre de usuario"></div>
        <div class="form-group"><label>Contraseña</label><input type="password" name="contraseña" placeholder="Contraseña"></div>
        <div class="form-group"><label>Número de Empleado (Teléfono)</label><input type="text" name="numero_empleado" placeholder="Ej: 5511864680"></div>
        <div class="form-group"><label>Fecha</label><input type="date" name="fecha"></div>
        <div class="form-group"><label>Calificación (1-5)</label><input type="number" name="calificacion" min="1" max="5"></div>
        <div class="form-group"><label>Agendar Llamada</label><select name="agendar_llamada"><option value="No">No</option><option value="Si">Sí</option></select></div>
        <div class="form-group"><label>Nombre Completo</label><input type="text" name="nombre_completo" placeholder="Nombre completo"></div>
        <div class="form-group"><label>Sexo</label><select name="sexo"><option value="M">M</option><option value="F">F</option><option value="No Binario">No Binario</option></select></div>
        <div class="form-group"><label>¿Cuenta con Seguridad Social?</label><select name="cuenta_seg_social"><option value="No">No</option><option value="Si">Sí</option></select></div>
        <div class="form-group"><label>Titular de Seguridad Social</label><input type="text" name="titular_seg_social"></div>
        <div class="form-group"><label>Fecha de Nacimiento</label><input type="date" name="fecha_nacimiento"></div>
        <div class="form-group"><label>Edad (Años)</label><input type="number" name="edad_anios"></div>
        <div class="form-group"><label>Estado Civil</label><select name="estado_civil"><option value="">Seleccione</option><option value="Soltero(a)">Soltero(a)</option><option value="Casado(a)">Casado(a)</option><option value="Divorciado(a)">Divorciado(a)</option><option value="Viudo(a)">Viudo(a)</option></select></div>
        <div class="form-group"><label>Teléfono Celular</label><input type="text" name="telefono_celular"></div>
        <div class="form-group"><label>Teléfono para Recados</label><input type="text" name="telefono_recados"></div>
        <div class="form-group"><label>Servicio Repartido</label><input type="text" name="servicio_repartido"></div>
        <div class="form-group"><label>Referencia</label><input type="text" name="referencia"></div>
        <div class="form-group"><label>¿A través de qué Red Social se enteró?</label><select name="red_social"><option value="">Seleccione</option><option value="Facebook">Facebook</option><option value="Instagram">Instagram</option><option value="WhatsApp">WhatsApp</option><option value="YouTube">YouTube</option><option value="TikTok">TikTok</option><option value="Otra">Otra</option></select></div>
        <div class="form-group"><label>Número de Seguridad Social</label><input type="text" name="numero_seguridad_social"></div>
        <div class="form-group"><label>Afiliación</label><input type="text" name="afiliacion"></div>
        <div class="form-group"><label>Estudio Socioeconómico</label><input type="text" name="estudio_socioeconomico"></div>
      </div>
      <!-- TAB 1 -->
      <div class="tab-panel">
        <div class="form-group"><label>CURP</label><input type="text" name="curp"></div>
        <div class="form-group"><label>Nombre de Seguridad Social</label><input type="text" name="nombre_seg_social"></div>
        <div class="form-group"><label>¿Cuenta con Seguro Social?</label><select name="cuenta_con_seguro"><option value="No">No</option><option value="Si">Sí</option></select></div>
        <div class="form-group"><label>Compañía de Seguros</label><input type="text" name="compania_seguros"></div>
        <div class="form-group"><label>Estrato Socioeconómico</label><input type="text" name="estrato_socioeconomico"></div>
        <div class="form-group"><label>Rango</label><input type="text" name="rango"></div>
        <div class="form-group"><label>Parentesco</label><input type="text" name="parentesco"></div>
        <div class="form-group"><label>Escolaridad Padre</label><input type="text" name="escolaridad_padre"></div>
        <div class="form-group"><label>Nombre del Padre</label><input type="text" name="nombre_padre"></div>
        <div class="form-group"><label>Nombre de la Madre</label><input type="text" name="nombre_madre"></div>
        <div class="form-group"><label>Escolaridad de la Madre</label><input type="text" name="escolaridad_madre"></div>
        <div class="form-group"><label>Ocupación del Padre</label><input type="text" name="ocupacion_padre"></div>
        <div class="form-group"><label>Ocupación de la Madre</label><input type="text" name="ocupacion_madre"></div>
        <div class="form-group"><label>Lugar de Trabajo del Padre</label><input type="text" name="lugar_trabajo_padre"></div>
        <div class="form-group"><label>Lugar de Trabajo de la Madre</label><input type="text" name="lugar_trabajo_madre"></div>
        <div class="form-group"><label>Estado Civil del Padre</label><input type="text" name="estado_civil_padre"></div>
        <div class="form-group"><label>Estado Civil de la Madre</label><input type="text" name="estado_civil_madre"></div>
        <div class="form-group"><label>Nombre del Responsable</label><input type="text" name="nombre_responsable"></div>
        <div class="form-group"><label>Número de Seguridad Social del Responsable</label><input type="text" name="numero_seg_social_responsable"></div>
        <div class="form-group"><label>Correo del Responsable</label><input type="email" name="correo_responsable"></div>
        <div class="form-group"><label>Celular del Responsable</label><input type="text" name="celular_responsable"></div>
      </div>
      <!-- TAB 2 -->
      <div class="tab-panel">
        <div class="form-group"><label>Nombre del Doctor</label><input type="text" name="nombre_doctor"></div>
        <div class="form-group"><label>¿Utiliza Implante?</label><select name="utiliza_implante"><option value="No">No</option><option value="Si">Sí</option></select></div>
        <div class="form-group"><label>Marca</label><input type="text" name="marca"></div>
        <div class="form-group"><label>Modelo</label><input type="text" name="modelo_medico"></div>
        <div class="form-group"><label>¿Conoce la causa?</label><select name="conoce_causa"><option value="No">No</option><option value="Si">Sí</option></select></div>
        <div class="form-group"><label>Causa</label><input type="text" name="causa"></div>
        <div class="form-group"><label>Electrodo</label><input type="text" name="electrodo"></div>
        <div class="form-group"><label>Configuración</label><input type="text" name="configuracion"></div>
        <div class="form-group"><label>Tipo de Implante</label><input type="text" name="tipo_implante"></div>
        <div class="form-group"><label>Médico Encendido</label><input type="text" name="medico_encendido"></div>
        <div class="form-group"><label>Fecha Encendido</label><input type="date" name="fecha_encendido"></div>
        <div class="form-group"><label>Mapeos</label><textarea name="mapeos"></textarea></div>
        <div class="form-group"><label>Expediente</label><input type="text" name="expediente"></div>
        <div class="form-group"><label>Firmó Formulario</label><select name="firmo_formulario"><option value="No">No</option><option value="Si">Sí</option></select></div>
        <div class="form-group"><label>Hospital</label><input type="text" name="hospital"></div>
        <div class="form-group"><label>Estado</label><input type="text" name="estado"></div>
        <div class="form-group"><label>Municipio</label><input type="text" name="municipio"></div>
        <div class="form-group"><label>Nombre del Cirujano</label><input type="text" name="nombre_cirujano"></div>
        <div class="form-group"><label>Nombre del Terapeuta (Paciente)</label><input type="text" name="nombre_terapeuta_paciente"></div>
        <div class="form-group"><label>Nombre del Audiologo</label><input type="text" name="nombre_audiologo"></div>
        <div class="form-group"><label>Centro de Implante</label><input type="text" name="centro_implante"></div>
        <div class="form-group"><label>¿Recibe Ayuda Auditiva?</label><select name="ayuda_auditiva"><option value="No">No</option><option value="Si">Sí</option></select></div>
      </div>
      <!-- TAB 3 -->
      <div class="tab-panel">
        <div class="form-group"><label>Nombre del Terapeuta (Rehabilitación)</label><input type="text" name="nombre_terapeuta_rehab"></div>
        <div class="form-group"><label>Tipo de Terapia</label><input type="text" name="tipo_terapia"></div>
        <div class="form-group"><label>Edad Auditiva</label><input type="number" name="edad_auditiva"></div>
        <div class="form-group"><label>Comunica</label><select name="comunica"><option value="Oral">Oral</option><option value="Señas">Señas</option><option value="Lector de labios">Lector de labios</option></select></div>
      </div>
    </div>
    <div class="save-container"><button type="submit" class="save-button">Save</button></div>
  </form>
</div>

</body></html>
""",
        contactos_html=contactos_html,
        bitacora_rows=bitacora_rows,
        agenda_html=agenda_html,
        informacion_html=informacion_html,
        donantes_html=donantes_html,
        email_section_html=email_section_html,
        q=q
    )

@app.route("/send_email", methods=["POST"])
def send_email():
    from_addr = request.form["from_email"].strip()
    to_list   = [addr.strip() for addr in request.form["to_list"].split(",") if addr.strip()]
    subject   = request.form["subject"]
    body      = request.form["body"]
    msg = Message(subject, sender=from_addr, recipients=to_list)
    msg.body     = body
    msg.html     = f"<pre>{body}</pre>"
    msg.reply_to = from_addr
    msg.extra_headers = {
        "Return-Path": f"<{from_addr}>",
        "List-Unsubscribe": f"<mailto:{from_addr}?subject=unsubscribe>",
        "X-Mailer": "MéxicoSinSorderaMailer/1.0 (Flask-Mail)"
    }
    for f in request.files.getlist("adjuntos"):
        if f and f.filename:
            data = f.read()                 # lee bytes
            msg.attach(
                filename=f.filename,        # nombre original
                content_type=f.mimetype,    # por ejemplo application/pdf
                data=data                   # contenido binario
        )

    try:
        mail.send(msg)
        flash("Correo masivo enviado correctamente")
    except Exception as e:
        flash("Error enviando correo: "+str(e))
    return redirect(url_for("dashboard"))

@app.route("/guardar_contacto", methods=["POST"])
def guardar_contacto():
    data = request.form.to_dict()
    conn = get_db_connection()
    conn.execute("""
        INSERT OR IGNORE INTO Usuario (id,nombre,correo,usuario,contraseña,numero_empleado,stars)
        VALUES (?,?,?,?,?,?,?)""", (
        data.get("idcontacto"),
        data.get("nombre_completo"),
        data.get("email"),
        data.get("usuario"),
        data.get("contraseña"),
        data.get("numero_empleado"),
        int(data.get("calificacion", 0))
    ))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

@app.route("/editar_contacto/<contacto_id>", methods=["GET","POST"])
def editar_contacto(contacto_id):
    conn = get_db_connection(); cur = conn.cursor()
    if request.method=="POST":
        nom = request.form["nombre"]
        tel = request.form["numero_empleado"]
        stars = int(request.form.get("stars", 0))
        cur.execute("UPDATE Usuario SET nombre=?, numero_empleado=?, stars=? WHERE id=?",
                    (nom, tel, stars, contacto_id))
        conn.commit(); conn.close()
        flash("Contacto actualizado")
        return redirect(url_for("dashboard"))
    cur.execute("SELECT nombre, numero_empleado, stars FROM Usuario WHERE id=?", (contacto_id,))
    ux = cur.fetchone(); conn.close()
    return render_template_string(f"""
<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Editar Contacto</title>
<style>body{{font-family:Arial,sans-serif;padding:20px}}.btn{{background:#2ebf91;color:#fff;border:none;padding:8px;border-radius:4px}}</style>
</head><body>
  <h2>Editar Contacto</h2>
  <form method="POST">
    <label>Nombre</label><input type="text" name="nombre" value="{ux['nombre']}" required><br><br>
    <label>Teléfono</label><input type="text" name="numero_empleado" value="{ux['numero_empleado']}" required><br><br>
    <label>Calificación</label><input type="number" name="stars" value="{ux['stars']}" min="1" max="5" required><br><br>
    <button type="submit" class="btn">Actualizar</button>
  </form>
</body></html>""")

@app.route("/eliminar_contacto/<contacto_id>")
def eliminar_contacto(contacto_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM Usuario WHERE id=?", (contacto_id,))
    conn.commit(); conn.close()
    flash("Contacto eliminado")
    return redirect(url_for("dashboard"))

@app.route("/whatsapp_mensaje/<contacto_id>")
def whatsapp_mensaje(contacto_id):
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT numero_empleado FROM Usuario WHERE id=?", (contacto_id,))
    r = cur.fetchone(); conn.close()
    if not r:
        flash("Contacto no encontrado"); return redirect(url_for("dashboard"))
    p = format_phone(r["numero_empleado"])
    try:
        kit.sendwhatmsg_instantly(p, "Hola, este es un mensaje de México Sin Sordera AC.", wait_time=20, tab_close=True)
        flash("WhatsApp enviado")
    except Exception as e:
        flash("Error enviando WhatsApp: "+str(e))
    return redirect(url_for("dashboard"))

@app.route("/llamar/<contacto_id>")
def llamar(contacto_id):
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT numero_empleado FROM Usuario WHERE id=?", (contacto_id,))
    r = cur.fetchone(); conn.close()
    if not r:
        flash("Contacto no encontrado"); return redirect(url_for("dashboard"))
    phone = format_phone(r["numero_empleado"])
    payload = {
      "method":"ttsCallout","ttsCallout":{
        "cli":SINCH_CLI_NUMBER,"domain":"pstn",
        "destination":{"type":"number","endpoint":phone},
        "locale":"es-MX","prompts":"#tts[Hola, esta es una llamada de México Sin Sordera A.C.]"
      }
    }
    creds = f"{SINCH_APP_KEY}:{SINCH_APP_SECRET}"
    headers = {
      "Content-Type":"application/json",
      "Authorization":"Basic "+base64.b64encode(creds.encode()).decode()
    }
    try:
        resp = requests.post("https://calling.api.sinch.com/calling/v1/callouts",
                             headers=headers, data=json.dumps(payload))
        resp.raise_for_status()
        now = datetime.now()
        ts = now.strftime("%d-%m-%Y %H:%M")
        fc = now.strftime("%Y-%m-%d %H:%M")
        obs = f"Llamada saliente a {phone}"
        conn2 = get_db_connection()
        conn2.execute("INSERT INTO Bitacora (timestamp,fechallamada,obs) VALUES (?,?,?)", (ts,fc,obs))
        conn2.commit(); conn2.close()
        flash("Llamada iniciada")
    except Exception as e:
        flash("Error iniciando llamada: "+str(e))
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión")
    return redirect(url_for("landing"))

if __name__=="__main__":
    import sys
    if len(sys.argv)>1 and sys.argv[1]=="populate":
        create_and_populate()
    app.run(debug=True)
