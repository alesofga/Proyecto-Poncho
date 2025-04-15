import sqlite3
from faker import Faker
import random
from datetime import date
import uuid
import urllib.parse
from flask import Flask, request, redirect, render_template_string, session, url_for, flash
import pywhatkit as kit
from twilio.rest import Client
import os

DB_NAME = 'mexico_sinsordera.db'

CREATE_TABLES = [
    ("Usuario",
     '''
     CREATE TABLE IF NOT EXISTS Usuario (
         id TEXT PRIMARY KEY,
         nombre TEXT,
         correo TEXT,
         usuario TEXT,
         contraseña TEXT,
         numero_empleado TEXT,
         stars INTEGER
     )'''),
    ("Bitacora",
     '''
     CREATE TABLE IF NOT EXISTS Bitacora (
         idbitacora INTEGER PRIMARY KEY,
         timestamp TEXT,
         fechallamada TEXT,
         obs TEXT
     )'''),
    ("Agenda",
     '''
     CREATE TABLE IF NOT EXISTS Agenda (
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         nombre TEXT,
         phone TEXT,
         img TEXT
     )'''),
    ("Padres",
     '''
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
     )'''),
    ("Diagnostico",
     '''
     CREATE TABLE IF NOT EXISTS Diagnostico (
         id TEXT,
         nombre_candidato TEXT,
         nombre_doctor TEXT,
         medico_especialista TEXT,
         PRIMARY KEY(id, nombre_candidato)
     )'''),
    ("Implante",
     '''
     CREATE TABLE IF NOT EXISTS Implante (
         id TEXT,
         nombre_candidato TEXT,
         utiliza_implante TEXT,
         marca TEXT,
         modelo TEXT,
         conoce_causa TEXT,
         causa TEXT,
         PRIMARY KEY(id, nombre_candidato)
     )'''),
    ("Beneficiario",
     '''
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
     )'''),
    ("Responsable",
     '''
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
     )'''),
    ("Rehabilitacion",
     '''
     CREATE TABLE IF NOT EXISTS Rehabilitacion (
         id TEXT,
         nombre_terapeuta TEXT,
         tipo_terapia TEXT,
         edad_auditiva INTEGER,
         comunica TEXT,
         PRIMARY KEY(id, nombre_terapeuta)
     )'''),
    ("Referencias",
     '''
     CREATE TABLE IF NOT EXISTS Referencias (
         id TEXT PRIMARY KEY,
         medio_conocer TEXT,
         red_social TEXT,
         referencia TEXT
     )'''),
    ("Cirugia",
     '''
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
     )'''),
    ("Paciente",
     '''
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
     )'''),
    ("Donantes",
     '''
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
     )'''),
     ("Historial",
     '''
     CREATE TABLE IF NOT EXISTS Historial (
         id TEXT PRIMARY KEY,
         nombre TEXT,
         numero TEXT,
         fecha_registro TEXT
     )''')
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

    for _ in range(n_users):
        uid = fake.bothify(text='###-##-?#?')
        nombre = fake.name()
        correo = fake.email()
        usuario = fake.user_name()
        contraseña = fake.password(length=10)
        numero_empleado = str(fake.random_number(digits=10))
        stars = random.randint(1, 5)
        c.execute('INSERT OR IGNORE INTO Usuario VALUES (?,?,?,?,?,?,?)', 
                  (uid, nombre, correo, usuario, contraseña, numero_empleado, stars))
        c.execute('INSERT OR IGNORE INTO Historial (id, nombre, numero, fecha_registro) VALUES (?,?,?,?)',
                  (uid, nombre, numero_empleado, date.today().isoformat()))

    for _ in range(n_records):
        idb = fake.random_int(1000, 9999)
        ts = fake.date_time_between('-1y', 'now').strftime('%d-%m-%Y %H:%M')
        fc = fake.date_time_between('-1y', 'now').strftime('%Y-%m-%d %H:%M')
        obs = fake.sentence(nb_words=6)
        c.execute('INSERT OR IGNORE INTO Bitacora VALUES (?,?,?,?)', (idb, ts, fc, obs))

    sample_imgs = ['person1.jpg', 'person2.jpeg', 'person3.jpeg', 'person4.jpeg', 'person5.jpeg', 'person6.jpeg']
    for _ in range(n_records):
        c.execute('INSERT INTO Agenda (nombre, phone, img) VALUES (?,?,?)',
                  (fake.name(), fake.phone_number(), random.choice(sample_imgs)))

    for _ in range(n_records):
        beneficiary_id = fake.bothify('B##??')
        beneficiary_name = fake.name()
        dob = fake.date_of_birth(minimum_age=1, maximum_age=90)
        edad = date.today().year - dob.year
        c.execute('INSERT OR IGNORE INTO Beneficiario VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (
            beneficiary_id, beneficiary_name, dob.isoformat(), fake.city(), edad,
            random.choice(['M','F','No Binario']), fake.job(), fake.job(), fake.bothify('CURP##########'),
            fake.bothify('SSS-####'), fake.company(), random.choice(['Sí','No']), fake.company(),
            random.choice(['Sí','No']), random.choice(['A','B','C']), fake.word()
        ))
        if edad < 18:
            c.execute('INSERT OR IGNORE INTO Padres VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (
                beneficiary_id, beneficiary_name,
                fake.name(), fake.name(),
                fake.job(), fake.job(),
                fake.company(), fake.company(),
                fake.city(), fake.city(),
                random.choice(['Soltero(a)','Casado(a)','Divorciado(a)']),
                random.choice(['Soltero(a)','Casado(a)','Divorciado(a)'])
            ))

    for _ in range(n_records):
        c.execute('INSERT OR IGNORE INTO Diagnostico VALUES (?,?,?,?)', (
            fake.bothify('D##??'), fake.name(), fake.name(), fake.job()
        ))
    brands = ['Cochlear','Med-El','Advanced Bionics']
    for _ in range(n_records):
        utiliza = random.choice(['Sí','No'])
        conoce = random.choice(['Sí','No'])
        c.execute('INSERT OR IGNORE INTO Implante VALUES (?,?,?,?,?,?,?)', (
            fake.bothify('I##??'), fake.name(), utiliza,
            random.choice(brands), fake.bothify('M-###'), conoce, fake.sentence()
        ))
    for _ in range(n_records):
        c.execute('INSERT OR IGNORE INTO Responsable VALUES (?,?,?,?,?,?,?,?)', (
            fake.bothify('R##??'), fake.name(), fake.name(), random.choice(['Padre','Madre','Tutor']),
            random.choice(['Sí','No']), fake.bothify('SSS-####'), fake.email(), fake.phone_number()
        ))
    for _ in range(n_records):
        c.execute('INSERT OR IGNORE INTO Rehabilitacion VALUES (?,?,?,?,?)', (
            fake.bothify('RH##'), fake.name(), random.choice(['Auditiva','Lenguaje','Fonoaudiología']),
            random.randint(1,10), random.choice(['Oral','Señas','Lector de labios'])
        ))
    for _ in range(n_records):
        c.execute('INSERT OR IGNORE INTO Referencias VALUES (?,?,?,?)', (
            fake.bothify('REF##'), random.choice(['Web','Evento','Amigo']),
            random.choice(['Facebook','Instagram','TikTok']), fake.sentence()
        ))
    for _ in range(n_records):
        c.execute('INSERT OR IGNORE INTO Cirugia VALUES (?,?,?,?,?,?,?,?)', (
            fake.bothify('CIR##'), fake.bothify('NC-###'), fake.word(), fake.sentence(),
            random.choice(brands), fake.name(), fake.date_this_decade().isoformat(), fake.text(max_nb_chars=20)
        ))
    for _ in range(n_records):
        c.execute('INSERT OR IGNORE INTO Paciente VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (
            fake.bothify('P##??'), fake.name(), fake.bothify('EXP-#####'), random.choice(['Sí','No']),
            fake.company(), fake.state(), fake.city(), fake.name(), fake.name(), fake.name(),
            fake.company(), random.choice(['Sí','No'])
        ))

    conn.commit()
    conn.close()


app = Flask(__name__)
app.secret_key = 'your_secret_key'  

import os

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")

@app.route("/")
def landing():
    landing_html = """
    <!DOCTYPE html>
    <html lang="es">
      <head>
        <meta charset="UTF-8">
        <title>Bienvenido - México Sin Sordera AC</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
          body { font-family: Arial, sans-serif; background-color: #f5f5f5;
                 display: flex; align-items: center; justify-content: center;
                 height: 100vh; margin: 0; }
          .container { text-align: center; background: #fff; padding: 40px; border-radius: 8px;
                       box-shadow: 0 0 10px rgba(0,0,0,0.1); }
          a { text-decoration: none; color: #fff; background: #2ebf91; padding: 10px 20px;
             border-radius: 4px; margin: 10px; display: inline-block; }
          a:hover { background: #28a17b; }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>Bienvenido a México Sin Sordera AC</h1>
          <p>Por favor, inicia sesión o regístrate para continuar.</p>
          <a href="/login">Login</a>
          <a href="/register">Registro</a>
        </div>
      </body>
    </html>
    """
    return render_template_string(landing_html)

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    
    q = request.args.get("q", "").strip()
    conn = get_db_connection()
    cur = conn.cursor()
    if q:
        cur.execute("SELECT id, nombre, stars, numero_empleado FROM Usuario WHERE nombre LIKE ? OR numero_empleado LIKE ?", 
                    (f"%{q}%", f"%{q}%"))
    else:
        cur.execute("SELECT id, nombre, stars, numero_empleado FROM Usuario")
    contactos = cur.fetchall()

    contactos_html = ""
    for c in contactos:
        stars_html = "".join('<i class="fa-solid fa-star"></i>' if i < c["stars"] else '<i class="fa-regular fa-star"></i>' for i in range(5))
        phone_formatted = format_phone(c["numero_empleado"]) if c["numero_empleado"] else ""
        contactos_html += f"""
        <div class="contact-row">
          <div class="contact-info">
            <i class="fa-solid fa-user-circle contact-icon"></i>
            <div>
              <div class="contact-phone">{phone_formatted}</div>
              <div class="contact-name">{c["nombre"]}</div>
            </div>
          </div>
          <div class="contact-stars">{stars_html}</div>
          <div class="contact-actions">
            <a href="/editar_contacto/{c['id']}"><i class="fa-solid fa-pen edit-icon"></i></a>
            <a href="/eliminar_contacto/{c['id']}" onclick="return confirm('¿Estás seguro de eliminar este contacto?');">
              <i class="fa-solid fa-trash-can delete-icon"></i>
            </a>
            <a href="/whatsapp_mensaje/{c['id']}" title="Enviar WhatsApp">
              <i class="fa-brands fa-whatsapp"></i>
            </a>
            <a href="/llamar/{c['id']}" title="Realizar llamada">
              <i class="fa-solid fa-phone"></i>
            </a>
          </div>
        </div>
        """
    
    cur.execute("""
        SELECT b.*, 
               p.nombre_padre, p.nombre_madre, 
               p.escolaridad_padre, p.escolaridad_madre, 
               p.ocupacion_padre, p.ocupacion_madre, 
               p.lugar_trabajo_padre, p.lugar_trabajo_madre, 
               p.estado_civil_padre, p.estado_civil_madre
        FROM Beneficiario AS b
        LEFT JOIN Padres AS p ON b.id = p.id AND b.nombre_paciente = p.nombre_candidato
    """)
    beneficiarios = cur.fetchall()
    agenda_html = ""
    for ben in beneficiarios:
        row = dict(ben)
        ben_html = f"""
        <div class="beneficiario-card" style="border:1px solid #eee; padding:15px; margin-bottom:10px; border-radius:8px;">
          <h3>{row['nombre_paciente']}</h3>
          <p><strong>Fecha de Nacimiento:</strong> {row['fecha_nacimiento']}</p>
          <p><strong>Lugar de Nacimiento:</strong> {row['lugar_nacimiento']}</p>
          <p><strong>Edad:</strong> {row['edad']}</p>
          <p><strong>Sexo:</strong> {row['sexo']}</p>
          <p><strong>Escolaridad:</strong> {row['escolaridad']}</p>
          <p><strong>Ocupación:</strong> {row['ocupacion']}</p>
          <p><strong>CURP:</strong> {row['curp']}</p>
          <p><strong>Número de Seguridad Social:</strong> {row['numero_seguridad_social']}</p>
          <p><strong>Afiliación:</strong> {row['afiliacion']}</p>
          <p><strong>Cuenta Seguro:</strong> {row['cuenta_seguro']}</p>
          <p><strong>Compañia Seguro:</strong> {row['compania_seguro']}</p>
          <p><strong>Estudio Socioeconómico:</strong> {row['estudio_socio']}</p>
          <p><strong>Rango:</strong> {row['rango']}</p>
          <p><strong>Servicio:</strong> {row['servicio']}</p>
        """
        try:
            edad = int(row.get('edad', 0))
        except (ValueError, TypeError):
            edad = 0
        if edad < 18:
            ben_html += f"""
          <div class="padres-info" style="margin-top:10px; padding:10px; background:#f9f9f9; border-radius:6px;">
            <h4>Información de los Padres</h4>
            <p><strong>Nombre del Padre:</strong> {row.get('nombre_padre', 'No registrado')}</p>
            <p><strong>Nombre de la Madre:</strong> {row.get('nombre_madre', 'No registrado')}</p>
            <p><strong>Escolaridad del Padre:</strong> {row.get('escolaridad_padre', 'No registrado')}</p>
            <p><strong>Escolaridad de la Madre:</strong> {row.get('escolaridad_madre', 'No registrado')}</p>
            <p><strong>Ocupación del Padre:</strong> {row.get('ocupacion_padre', 'No registrado')}</p>
            <p><strong>Ocupación de la Madre:</strong> {row.get('ocupacion_madre', 'No registrado')}</p>
            <p><strong>Lugar de Trabajo del Padre:</strong> {row.get('lugar_trabajo_padre', 'No registrado')}</p>
            <p><strong>Lugar de Trabajo de la Madre:</strong> {row.get('lugar_trabajo_madre', 'No registrado')}</p>
            <p><strong>Estado Civil del Padre:</strong> {row.get('estado_civil_padre', 'No registrado')}</p>
            <p><strong>Estado Civil de la Madre:</strong> {row.get('estado_civil_madre', 'No registrado')}</p>
          </div>
            """
        ben_html += "</div>"
        agenda_html += ben_html

    cur.execute("SELECT idbitacora, timestamp, fechallamada, obs FROM Bitacora")
    bitacora_data = cur.fetchall()
    bitacora_rows = "".join(f"""
        <tr>
          <td>{b["idbitacora"]}</td>
          <td>{b["timestamp"]}</td>
          <td>{b["fechallamada"]}</td>
          <td>{b["obs"]}</td>
        </tr>
        """ for b in bitacora_data)
    
    informacion_html = f"""
    <div class="info-card">
      <h2>Información de la Asociación</h2>
      <p>
         <strong>México Sin Sordera AC</strong> es una asociación civil que apoya a las personas con pérdida auditiva a través de orientación, 
         distribución de aparatos, implantes cocleares y seguimiento en rehabilitación.
      </p>
      <p>
         Visita nuestro sitio oficial: 
         <a href="https://mexicosinsordera.org.mx/" target="_blank">mexicosinsordera.org.mx</a>
      </p>
      <div class="map-wrapper">
         <iframe src="https://www.google.com/maps?um=1&ie=UTF-8&fb=1&gl=mx&sa=X&geocode=KUHSLuY7_9GFMaLOZ7RP6dC4&daddr=Zacatecas+155-3er+Piso+Int+302,+Roma+Nte.,+Cuauhtémoc,+06700+Ciudad+de+M%C3%A9xico,+CDMX&output=embed" width="100%" height="300" style="border:0;" allowfullscreen="" loading="lazy"></iframe>
      </div>
    </div>
    """
    
    donantes = cur.fetchall()
    donantes_html = ""
    for don in donantes:
        row = dict(don)
        don_html = f"""
        <div class="donante-card" style="border:1px solid #eee; padding:15px; margin-bottom:10px; border-radius:8px;">
          <h3>{row.get('nombre_donante', 'Sin nombre')}</h3>
          <p><strong>Tipo de Donante:</strong> {row.get('tipo_donante', 'No especificado')}</p>
          <p><strong>Sector del Donante:</strong> {row.get('sector_donante', 'No especificado')}</p>
          <p><strong>Teléfono:</strong> {row.get('telefono_donante', 'No disponible')}</p>
          <p><strong>Correo Electrónico:</strong> {row.get('correo_donante', 'No disponible')}</p>
          <p><strong>Dirección:</strong> {row.get('direccion_donante', 'No disponible')}</p>
          <p><strong>Redes Sociales:</strong> {row.get('redes_sociales', 'No disponible')}</p>
          <p><strong>Observaciones:</strong> {row.get('observaciones_donante', 'Ninguna')}</p>
        </div>
        """
        donantes_html += don_html

    
    dashboard_html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="UTF-8">
      <title>México Sin Sordera AC</title>
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
      <style>
        /* RESET */
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; color: #333; }}
        .side-nav {{ width: 60px; background-color: #fff; border-right: 1px solid #ddd;
                     display: flex; flex-direction: column; align-items: center; padding-top: 10px; }}
        .nav-icon {{ width: 40px; height: 40px; border-radius: 50%; margin: 10px 0;
                     display: flex; align-items: center; justify-content: center; cursor: pointer; color: #666; }}
        .nav-icon:hover {{ background-color: #f0f0f0; color: #333; }}
        .nav-icon.active {{ background-color: #2ebf91; color: #fff; }}
        .app-container {{ display: flex; height: 100vh; width: 100vw; }}
        .main-content {{ flex: 1; display: flex; flex-direction: column; }}
        .header {{
          background-color: #fff; display: flex; align-items: center; padding: 0 20px;
          height: 60px; border-bottom: 1px solid #ddd;
        }}
        .logo-area {{ display: flex; align-items: center; margin-right: 20px; }}
        .logo-img {{ height: 40px; margin-right: 10px; }}
        .logo-text {{ font-weight: bold; font-size: 1.2em; color: #2ebf91; }}
        .search-bar {{ flex: 1; position: relative; max-width: 400px; }}
        .search-bar form {{ position: relative; }}
        .search-bar input {{
          width: 100%; padding: 8px 35px 8px 10px; border-radius: 4px; border: 1px solid #ccc;
        }}
        .search-bar i {{
          position: absolute; right: 10px; top: 50%; transform: translateY(-50%); color: #aaa;
        }}
        .add-button {{
          background-color: #2ebf91; color: #fff; border: none; padding: 8px 20px;
          border-radius: 4px; cursor: pointer; margin-left: 20px;
        }}
        .add-button:hover {{ background-color: #28a17b; }}
        .content-sections {{ flex: 1; overflow: auto; padding: 10px 20px; background-color: #fff; }}
        .section {{ display: none; }}
        .section.active {{ display: block; }}
        .contact-row {{
          display: flex; align-items: center; justify-content: space-between;
          padding: 8px 0; border-bottom: 1px solid #f0f0f0;
        }}
        .contact-info {{ display: flex; align-items: center; gap: 10px; }}
        .contact-icon {{ font-size: 1.8em; color: #2ebf91; }}
        .contact-phone {{ font-weight: 600; font-size: 0.9em; color: #555; }}
        .contact-name {{ font-size: 0.8em; color: #999; }}
        .contact-stars i {{ color: #FFD700; margin-right: 2px; }}
        .contact-actions a, .contact-actions i {{
          margin-left: 10px; color: #888; cursor: pointer; text-decoration: none;
        }}
        .contact-actions a:hover, .contact-actions i:hover {{ color: #333; }}
        .bitacora-table {{ width: 100%; border-collapse: collapse; }}
        .bitacora-table th, .bitacora-table td {{
          border: 1px solid #eee; padding: 8px; font-size: 0.9em;
        }}
        .bitacora-table th {{ background-color: #fafafa; text-align: left; color: #666; }}
        .agenda-row {{
          display: flex; align-items: center; justify-content: space-between;
          padding: 8px 0; border-bottom: 1px solid #f0f0f0;
        }}
        .agenda-info {{ display: flex; align-items: center; gap: 10px; }}
        .agenda-img {{ width: 40px; height: 40px; border-radius: 50%; object-fit: cover; }}
        .agenda-details {{ display: flex; flex-direction: column; }}
        .agenda-name {{ font-weight: 600; font-size: 0.9em; color: #555; }}
        .agenda-phone {{ font-size: 0.8em; color: #999; }}
        .agenda-actions i {{ margin-left: 15px; font-size: 1.2em; color: #666; cursor: pointer; }}
        .agenda-actions i:hover {{ color: #333; }}
        .form-container {{
          position: fixed; top: 0; right: -100%; width: 30%; max-width: 500px; height: 100%;
          background-color: #fff; box-shadow: -2px 0 10px rgba(0,0,0,0.2);
          transition: right 0.3s ease; overflow-y: auto; z-index: 9999;
        }}
        .form-container.show {{ right: 0; }}
        .form-header {{
          display: flex; justify-content: space-between; align-items: center;
          padding: 15px; border-bottom: 1px solid #ddd;
        }}
        .form-header h3 {{ margin: 0; font-size: 1.2em; color: #2ebf91; }}
        .close-btn {{
          background: #f44336; color: #fff; border: none; border-radius: 4px;
          padding: 5px 10px; cursor: pointer;
        }}
        .close-btn:hover {{ background: #d73225; }}
        .form-body {{ padding: 15px; }}
        .tab-buttons {{ display: flex; gap: 5px; margin-bottom: 10px; }}
        .tab-button {{
          flex: 1; padding: 8px; border: none; background-color: #eee;
          cursor: pointer; border-radius: 4px; font-size: 0.9em; color: #666;
        }}
        .tab-button.active {{ background-color: #2ebf91; color: #fff; }}
        .tab-panel {{ display: none; }}
        .tab-panel.active {{ display: block; }}
        .form-group {{ margin-bottom: 10px; }}
        .form-group label {{ display: block; margin-bottom: 5px; font-size: 0.9em; color: #333; }}
        .form-group input,
        .form-group select,
        .form-group textarea {{
          width: 100%; padding: 8px; font-size: 0.9em; border: 1px solid #ccc; border-radius: 4px;
        }}
        .save-container {{ text-align: right; margin: 15px; }}
        .save-button {{
          background-color: #2ebf91; color: #fff; border: none; padding: 8px 15px;
          border-radius: 4px; cursor: pointer;
        }}
        .save-button:hover {{ background-color: #28a17b; }}
      </style>
      <script>
        function selectNav(index) {{
          const icons = document.querySelectorAll('.nav-icon');
          icons.forEach(icon => icon.classList.remove('active'));
          icons[index].classList.add('active');
          const sections = document.querySelectorAll('.section');
          sections.forEach(sec => sec.classList.remove('active'));
          sections[index].classList.add('active');
        }}
        function openForm() {{ document.getElementById('form-container').classList.add('show'); }}
        function closeForm() {{ document.getElementById('form-container').classList.remove('show'); }}
        function showTab(tabIndex) {{
          const panels = document.querySelectorAll('.tab-panel');
          const buttons = document.querySelectorAll('.tab-button');
          panels.forEach((p, i) => {{
            p.classList.remove('active');
            buttons[i].classList.remove('active');
          }});
          panels[tabIndex].classList.add('active');
          buttons[tabIndex].classList.add('active');
        }}
      </script>
    </head>
    <body>
      <div class="app-container">
        <div class="side-nav">
          <div class="nav-icon active" onclick="selectNav(0)"><i class="fa-solid fa-address-book"></i></div>
          <div class="nav-icon" onclick="selectNav(1)"><i class="fa-solid fa-phone"></i></div>
          <div class="nav-icon" onclick="selectNav(2)"><i class="fa-solid fa-calendar"></i></div>
          <div class="nav-icon" onclick="selectNav(3)"><i class="fa-solid fa-circle-info"></i></div>
          <div class="nav-icon" onclick="selectNav(4)"><i class="fa-solid fa-table-cells"></i></div>
        </div>
        <div class="main-content">
          <div class="header">
            <div class="logo-area">
              <img src="/static/images/logo.jpeg" alt="Logo" class="logo-img">
              <div class="logo-text">México Sin Sordera AC</div>
            </div>
            <div class="search-bar">
              <form action="/dashboard" method="GET">
                <input type="text" name="q" placeholder="Search Contacto..." value="{q}">
                <i class="fa-solid fa-magnifying-glass"></i>
              </form>
            </div>
            <button class="add-button" onclick="openForm()">
              <i class="fa-solid fa-plus"></i> Add
            </button>
          </div>
          <div class="content-sections">
            <div class="section active">
              <h2>Contactos</h2>
              {contactos_html}
            </div>
            <div class="section">
              <h2>Bitácora de llamadas</h2>
              <table class="bitacora-table">
                <thead>
                  <tr>
                    <th>IDBitácora</th>
                    <th>TimeStamp</th>
                    <th>Fecha Llamada</th>
                    <th>Observaciones</th>
                  </tr>
                </thead>
                <tbody>
                  {bitacora_rows}
                </tbody>
              </table>
            </div>
            <div class="section">
              <h2>Agenda - Información de Beneficiarios</h2>
              {agenda_html}
            </div>
            <div class="section">
              {informacion_html}
            </div>
            <div class="section">
              {donantes_html}
            </div>
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
            <div class="tab-panel active">
              <div class="form-group">
                <label>Email</label>
                <input type="email" name="email" placeholder="correo@ejemplo.com">
              </div>
              <div class="form-group">
                <label>IDContacto</label>
                <input type="text" name="idcontacto" placeholder="Ej: 127-43-F4++">
              </div>
              <div class="form-group">
                <label>Usuario</label>
                <input type="text" name="usuario" placeholder="Nombre de usuario">
              </div>
              <div class="form-group">
                <label>Contraseña</label>
                <input type="password" name="contraseña" placeholder="Contraseña">
              </div>
              <div class="form-group">
                <label>Número de Empleado (Teléfono)</label>
                <input type="text" name="numero_empleado" placeholder="Ej: 5511864680">
              </div>
              <div class="form-group">
                <label>Fecha</label>
                <input type="date" name="fecha">
              </div>
              <div class="form-group">
                <label>Calificación (1-5)</label>
                <input type="number" name="calificacion" min="1" max="5" placeholder="1-5">
              </div>
              <div class="form-group">
                <label>Agendar Llamada</label>
                <select name="agendar_llamada">
                  <option value="No">No</option>
                  <option value="Si">Sí</option>
                </select>
              </div>
              <div class="form-group">
                <label>Nombre Completo</label>
                <input type="text" name="nombre_completo" placeholder="Ej: Valentina del Pilar Acuña">
              </div>
              <div class="form-group">
                <label>Sexo</label>
                <select name="sexo">
                  <option value="M">M</option>
                  <option value="F">F</option>
                  <option value="No Binario">No Binario</option>
                </select>
              </div>
              <div class="form-group">
                <label>¿Cuenta con Seguridad Social?</label>
                <select name="cuenta_seg_social">
                  <option value="No">No</option>
                  <option value="Si">Sí</option>
                </select>
              </div>
              <div class="form-group">
                <label>Titular de Seguridad Social</label>
                <input type="text" name="titular_seg_social">
              </div>
              <div class="form-group">
                <label>Fecha de Nacimiento</label>
                <input type="date" name="fecha_nacimiento">
              </div>
              <div class="form-group">
                <label>Edad (Años)</label>
                <input type="number" name="edad_anios" placeholder="Ej: 35">
              </div>
              <div class="form-group">
                <label>Estado Civil</label>
                <select name="estado_civil">
                  <option value="">Seleccione</option>
                  <option value="Soltero(a)">Soltero(a)</option>
                  <option value="Casado(a)">Casado(a)</option>
                  <option value="Divorciado(a)">Divorciado(a)</option>
                  <option value="Viudo(a)">Viudo(a)</option>
                </select>
              </div>
              <div class="form-group">
                <label>Teléfono Celular</label>
                <input type="text" name="telefono_celular" placeholder="3001234567">
              </div>
              <div class="form-group">
                <label>Teléfono para Recados</label>
                <input type="text" name="telefono_recados" placeholder="3107654321">
              </div>
              <div class="form-group">
                <label>Servicio Repartido</label>
                <input type="text" name="servicio_repartido">
              </div>
              <div class="form-group">
                <label>Referencia</label>
                <input type="text" name="referencia">
              </div>
              <div class="form-group">
                <label>¿A través de qué Red Social se enteró?</label>
                <select name="red_social">
                  <option value="">Seleccione</option>
                  <option value="Facebook">Facebook</option>
                  <option value="Instagram">Instagram</option>
                  <option value="WhatsApp">WhatsApp</option>
                  <option value="YouTube">YouTube</option>
                  <option value="TikTok">TikTok</option>
                  <option value="Otra">Otra</option>
                </select>
              </div>
              <div class="form-group">
                <label>Número de Seguridad Social</label>
                <input type="text" name="numero_seguridad_social">
              </div>
              <div class="form-group">
                <label>Afiliación</label>
                <input type="text" name="afiliacion">
              </div>
              <div class="form-group">
                <label>Estudio Socioeconómico</label>
                <input type="text" name="estudio_socioeconomico">
              </div>
            </div>
            <div class="tab-panel">
              <div class="form-group">
                <label>CURP</label>
                <input type="text" name="curp">
              </div>
              <div class="form-group">
                <label>Nombre de Seguridad Social</label>
                <input type="text" name="nombre_seg_social">
              </div>
              <div class="form-group">
                <label>¿Cuenta con Seguro Social?</label>
                <select name="cuenta_con_seguro">
                  <option value="No">No</option>
                  <option value="Si">Sí</option>
                </select>
              </div>
              <div class="form-group">
                <label>Compañía de Seguros</label>
                <input type="text" name="compania_seguros">
              </div>
              <div class="form-group">
                <label>Estrato Socioeconómico</label>
                <input type="text" name="estrato_socioeconomico">
              </div>
              <div class="form-group">
                <label>Rango</label>
                <input type="text" name="rango">
              </div>
              <div class="form-group">
                <label>Parentesco</label>
                <input type="text" name="parentesco">
              </div>
              <div class="form-group">
                <label>Escolaridad Padre</label>
                <input type="text" name="escolaridad_padre">
              </div>
              <div class="form-group">
                <label>Nombre del Padre</label>
                <input type="text" name="nombre_padre">
              </div>
              <div class="form-group">
                <label>Nombre de la Madre</label>
                <input type="text" name="nombre_madre">
              </div>
              <div class="form-group">
                <label>Escolaridad de la Madre</label>
                <input type="text" name="escolaridad_madre">
              </div>
              <div class="form-group">
                <label>Ocupación del Padre</label>
                <input type="text" name="ocupacion_padre">
              </div>
              <div class="form-group">
                <label>Ocupación de la Madre</label>
                <input type="text" name="ocupacion_madre">
              </div>
              <div class="form-group">
                <label>Lugar de Trabajo del Padre</label>
                <input type="text" name="lugar_trabajo_padre">
              </div>
              <div class="form-group">
                <label>Lugar de Trabajo de la Madre</label>
                <input type="text" name="lugar_trabajo_madre">
              </div>
              <div class="form-group">
                <label>Estado Civil del Padre</label>
                <input type="text" name="estado_civil_padre">
              </div>
              <div class="form-group">
                <label>Estado Civil de la Madre</label>
                <input type="text" name="estado_civil_madre">
              </div>
              <div class="form-group">
                <label>Nombre del Responsable</label>
                <input type="text" name="nombre_responsable">
              </div>
              <div class="form-group">
                <label>Número de Seguridad Social del Responsable</label>
                <input type="text" name="numero_seg_social_responsable">
              </div>
              <div class="form-group">
                <label>Correo del Responsable</label>
                <input type="email" name="correo_responsable">
              </div>
              <div class="form-group">
                <label>Celular del Responsable</label>
                <input type="text" name="celular_responsable">
              </div>
            </div>
            <div class="tab-panel">
              <div class="form-group">
                <label>Nombre del Doctor</label>
                <input type="text" name="nombre_doctor">
              </div>
              <div class="form-group">
                <label>¿Utiliza Implante?</label>
                <select name="utiliza_implante">
                  <option value="No">No</option>
                  <option value="Si">Sí</option>
                </select>
              </div>
              <div class="form-group">
                <label>Marca</label>
                <input type="text" name="marca">
              </div>
              <div class="form-group">
                <label>Modelo</label>
                <input type="text" name="modelo_medico">
              </div>
              <div class="form-group">
                <label>¿Conoce la causa?</label>
                <select name="conoce_causa">
                  <option value="No">No</option>
                  <option value="Si">Sí</option>
                </select>
              </div>
              <div class="form-group">
                <label>Causa</label>
                <input type="text" name="causa">
              </div>
              <div class="form-group">
                <label>Electrodo</label>
                <input type="text" name="electrodo">
              </div>
              <div class="form-group">
                <label>Configuración</label>
                <input type="text" name="configuracion">
              </div>
              <div class="form-group">
                <label>Tipo de Implante</label>
                <input type="text" name="tipo_implante">
              </div>
              <div class="form-group">
                <label>Médico Encendido</label>
                <input type="text" name="medico_encendido">
              </div>
              <div class="form-group">
                <label>Fecha Encendido</label>
                <input type="date" name="fecha_encendido">
              </div>
              <div class="form-group">
                <label>Mapeos</label>
                <textarea name="mapeos"></textarea>
              </div>
              <div class="form-group">
                <label>Expediente</label>
                <input type="text" name="expediente">
              </div>
              <div class="form-group">
                <label>Firmó Formulario</label>
                <select name="firmo_formulario">
                  <option value="No">No</option>
                  <option value="Si">Sí</option>
                </select>
              </div>
              <div class="form-group">
                <label>Hospital</label>
                <input type="text" name="hospital">
              </div>
              <div class="form-group">
                <label>Estado</label>
                <input type="text" name="estado">
              </div>
              <div class="form-group">
                <label>Municipio</label>
                <input type="text" name="municipio">
              </div>
              <div class="form-group">
                <label>Nombre del Cirujano</label>
                <input type="text" name="nombre_cirujano">
              </div>
              <div class="form-group">
                <label>Nombre del Terapeuta (Paciente)</label>
                <input type="text" name="nombre_terapeuta_paciente">
              </div>
              <div class="form-group">
                <label>Nombre del Audiologo</label>
                <input type="text" name="nombre_audiologo">
              </div>
              <div class="form-group">
                <label>Centro de Implante</label>
                <input type="text" name="centro_implante">
              </div>
              <div class="form-group">
                <label>¿Recibe Ayuda Auditiva?</label>
                <select name="ayuda_auditiva">
                  <option value="No">No</option>
                  <option value="Si">Sí</option>
                </select>
              </div>
            </div>
            <div class="tab-panel">
              <div class="form-group">
                <label>Nombre del Terapeuta (Rehabilitación)</label>
                <input type="text" name="nombre_terapeuta_rehab">
              </div>
              <div class="form-group">
                <label>Tipo de Terapia</label>
                <input type="text" name="tipo_terapia">
              </div>
              <div class="form-group">
                <label>Edad Auditiva</label>
                <input type="number" name="edad_auditiva">
              </div>
              <div class="form-group">
                <label>Comunica</label>
                <select name="comunica">
                  <option value="Oral">Oral</option>
                  <option value="Señas">Señas</option>
                  <option value="Lector de labios">Lector de labios</option>
                </select>
              </div>
            </div>
          </div>
          <div class="save-container">
            <button type="submit" class="save-button">Save</button>
          </div>
        </form>
      </div>
    </body>
    </html>
    """
    conn.close()
    return dashboard_html

def format_phone(phone):
    cleaned = "".join(ch for ch in phone if ch.isdigit())
    if not cleaned.startswith("52"):
        cleaned = "52" + cleaned
    return f"+{cleaned}"

@app.route("/guardar_contacto", methods=["POST"])
def guardar_contacto():
    data = request.form.to_dict()
    print("Datos recibidos:", data)
    idcontacto = data.get("idcontacto")
    nombre_completo = data.get("nombre_completo")
    email = data.get("email")
    usuario_field = data.get("usuario")
    contraseña_field = data.get("contraseña")
    numero_empleado = data.get("numero_empleado")
    try:
        stars = int(data.get("calificacion", 0))
    except ValueError:
        stars = 0
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO Usuario (id, nombre, correo, usuario, contraseña, numero_empleado, stars) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (idcontacto, nombre_completo, email, usuario_field, contraseña_field, numero_empleado, stars))
    conn.commit()
    conn.close()
    return redirect("/dashboard")

@app.route("/editar_contacto/<contacto_id>", methods=["GET", "POST"])
def editar_contacto(contacto_id):
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == "POST":
        nombre = request.form.get("nombre")
        numero_empleado = request.form.get("numero_empleado")
        stars = request.form.get("stars")
        try:
            stars = int(stars)
        except:
            stars = 0
        cur.execute("UPDATE Usuario SET nombre = ?, numero_empleado = ?, stars = ? WHERE id = ?",
                    (nombre, numero_empleado, stars, contacto_id))
        conn.commit()
        conn.close()
        flash("Contacto actualizado")
        return redirect(url_for("dashboard"))
    else:
        cur.execute("SELECT nombre, numero_empleado, stars FROM Usuario WHERE id = ?", (contacto_id,))
        contacto = cur.fetchone()
        conn.close()
        edit_html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Editar Contacto</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px; }}
                .form-container {{ max-width: 400px; margin: 0 auto; background: #fff; padding: 20px;
                                   border-radius: 4px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
                .form-group {{ margin-bottom: 15px; }}
                .form-group label {{ display: block; margin-bottom: 5px; }}
                .form-group input {{ width: 100%; padding: 8px; box-sizing: border-box; }}
                .btn {{ background-color: #2ebf91; color: #fff; padding: 10px 15px; border: none;
                       border-radius: 4px; cursor: pointer; }}
                .btn:hover {{ background-color: #28a17b; }}
            </style>
        </head>
        <body>
            <div class="form-container">
                <h2>Editar Contacto</h2>
                <form method="POST">
                    <div class="form-group">
                        <label>Nombre</label>
                        <input type="text" name="nombre" value="{contacto['nombre']}" required>
                    </div>
                    <div class="form-group">
                        <label>Número de Teléfono</label>
                        <input type="text" name="numero_empleado" value="{contacto['numero_empleado']}" required>
                    </div>
                    <div class="form-group">
                        <label>Calificación</label>
                        <input type="number" name="stars" value="{contacto['stars']}" min="1" max="5" required>
                    </div>
                    <button type="submit" class="btn">Actualizar</button>
                </form>
            </div>
        </body>
        </html>
        """
        return render_template_string(edit_html)

@app.route("/eliminar_contacto/<contacto_id>")
def eliminar_contacto(contacto_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Usuario WHERE id = ?", (contacto_id,))
    conn.commit()
    conn.close()
    flash("Contacto eliminado")
    return redirect(url_for("dashboard"))

@app.route("/whatsapp_mensaje/<contacto_id>")
def whatsapp_mensaje(contacto_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT numero_empleado FROM Usuario WHERE id = ?", (contacto_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        flash("Contacto no encontrado")
        return redirect(url_for("dashboard"))
    phone = row["numero_empleado"]
    formatted_phone = format_phone(phone)
    message = "Hola, este es un mensaje de México Sin Sordera AC."
    try:
        kit.sendwhatmsg_instantly(formatted_phone, message, wait_time=20, tab_close=True)
        flash("Mensaje de WhatsApp enviado a " + formatted_phone)
    except Exception as e:
        flash("Error enviando mensaje: " + str(e))
    return redirect(url_for("dashboard"))

@app.route("/llamar/<contacto_id>")
def llamar(contacto_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT numero_empleado FROM Usuario WHERE id = ?", (contacto_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        flash("Contacto no encontrado")
        return redirect(url_for("dashboard"))
    phone = row["numero_empleado"]
    formatted_phone = format_phone(phone)
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        call = client.calls.create(
            twiml='<Response><Say voice="alice" language="es-ES">Hola, esta es una llamada de México Sin Sordera AC.</Say></Response>',
            to=formatted_phone,
            from_=TWILIO_PHONE_NUMBER
        )
        flash("Llamada iniciada a " + formatted_phone)
    except Exception as e:
        flash("Error iniciando la llamada: " + str(e))
    return redirect(url_for("dashboard"))

@app.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        correo = request.form.get("correo")
        usuario_field = request.form.get("usuario")
        contraseña_field = request.form.get("contraseña")
        confirmar_contraseña = request.form.get("confirmar_contraseña")
        numero_empleado = request.form.get("numero_empleado")
        
        if contraseña_field != confirmar_contraseña:
            flash("Las contraseñas no coinciden")
            return redirect(url_for("register_page"))
        
        user_id = str(uuid.uuid4())
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO Usuario (id, nombre, correo, usuario, contraseña, numero_empleado, stars) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (user_id, nombre, correo, usuario_field, contraseña_field, numero_empleado, 0))
        cur.execute("INSERT INTO Historial (id, nombre, numero, fecha_registro) VALUES (?, ?, ?, ?)",
                    (user_id, nombre, numero_empleado, date.today().isoformat()))
        conn.commit()
        conn.close()
        flash("Registro exitoso, por favor inicia sesión")
        return redirect(url_for("login_page"))
    
    register_html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="UTF-8">
      <title>Registro</title>
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <style>
        body { font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px; }
        .form-container { max-width: 400px; margin: 0 auto; background: #fff; padding: 20px;
                          border-radius: 4px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; }
        .form-group input { width: 100%; padding: 8px; box-sizing: border-box; }
        .btn { background-color: #2ebf91; color: #fff; padding: 10px 15px; border: none;
               border-radius: 4px; cursor: pointer; }
        .btn:hover { background-color: #28a17b; }
      </style>
    </head>
    <body>
      <div class="form-container">
        <h2>Registro</h2>
        <form method="POST">
          <div class="form-group">
            <label>Nombre</label>
            <input type="text" name="nombre" required>
          </div>
          <div class="form-group">
            <label>Correo</label>
            <input type="email" name="correo" required>
          </div>
          <div class="form-group">
            <label>Usuario</label>
            <input type="text" name="usuario" required>
          </div>
          <div class="form-group">
            <label>Contraseña</label>
            <input type="password" name="contraseña" required>
          </div>
          <div class="form-group">
            <label>Confirmar Contraseña</label>
            <input type="password" name="confirmar_contraseña" required>
          </div>
          <div class="form-group">
            <label>Número de Empleado (Teléfono)</label>
            <input type="text" name="numero_empleado" placeholder="Ej: 5511864680">
          </div>
          <button type="submit" class="btn">Registrarse</button>
        </form>
        <p>¿Ya tienes cuenta? <a href="/login">Inicia sesión</a></p>
      </div>
    </body>
    </html>
    """
    return render_template_string(register_html)

@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        usuario_field = request.form.get("usuario")
        contraseña_field = request.form.get("contraseña")
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM Usuario WHERE usuario = ? AND contraseña = ?", (usuario_field, contraseña_field))
        user = cur.fetchone()
        conn.close()
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["nombre"]
            flash("Login exitoso")
            return redirect(url_for("dashboard"))
        else:
            flash("Credenciales incorrectas")
            return redirect(url_for("login_page"))
    
    login_html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="UTF-8">
      <title>Login</title>
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <style>
        body { font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px; }
        .form-container { max-width: 400px; margin: 0 auto; background: #fff; padding: 20px;
                          border-radius: 4px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; }
        .form-group input { width: 100%; padding: 8px; box-sizing: border-box; }
        .btn { background-color: #2ebf91; color: #fff; padding: 10px 15px; border: none;
               border-radius: 4px; cursor: pointer; }
        .btn:hover { background-color: #28a17b; }
      </style>
    </head>
    <body>
      <div class="form-container">
        <h2>Login</h2>
        <form method="POST">
          <div class="form-group">
            <label>Usuario</label>
            <input type="text" name="usuario" required>
          </div>
          <div class="form-group">
            <label>Contraseña</label>
            <input type="password" name="contraseña" required>
          </div>
          <button type="submit" class="btn">Iniciar Sesión</button>
        </form>
        <p>¿No tienes cuenta? <a href="/register">Regístrate</a></p>
      </div>
    </body>
    </html>
    """
    return render_template_string(login_html)

@app.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión")
    return redirect(url_for("landing"))

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'populate':
        create_and_populate()
    app.run(debug=True)