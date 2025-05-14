import sqlite3
from faker import Faker
import random
from datetime import date

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
         obs TEXT,
         recording_pdf TEXT
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
     ("Reminders", """
    CREATE TABLE IF NOT EXISTS Reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    tipo TEXT,
    mensaje TEXT,
    due_datetime TEXT,
    seen INTEGER DEFAULT 0,
    notified INTEGER DEFAULT 0
)"""),

]

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
        numero_empleado = str(fake.random_number(digits=5))
        stars = random.randint(1, 5)
        c.execute(
            'INSERT OR IGNORE INTO Usuario VALUES (?,?,?,?,?,?,?)',
            (uid, nombre, correo, usuario, contraseña, numero_empleado, stars)
        )

    for _ in range(n_records):
        idb = fake.random_int(1000, 9999)
        ts  = fake.date_time_between('-1y', 'now').strftime('%d-%m-%Y %H:%M')
        fc  = fake.date_time_between('-1y', 'now').strftime('%Y-%m-%d %H:%M')
        obs = fake.sentence(nb_words=6)
        # grabamos recording_pdf como NULL
        c.execute(
            '''
            INSERT OR IGNORE INTO Bitacora
            (idbitacora, timestamp, fechallamada, obs, recording_pdf)
            VALUES (?,?,?,?,?)
            ''',
            (idb, ts, fc, obs, None)
        )


    sample_imgs = ['person1.jpg', 'person2.jpeg', 'person3.jpeg', 'person4.jpeg']
    for _ in range(n_records):
        c.execute(
            'INSERT INTO Agenda (nombre, phone, img) VALUES (?,?,?)',
            (fake.name(), fake.phone_number(), random.choice(sample_imgs))
        )

    for _ in range(n_records):
        c.execute('INSERT OR IGNORE INTO Padres VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (
            fake.bothify('P##??'), fake.name(), fake.name(), fake.name(),
            fake.job(), fake.job(), fake.company(), fake.company(),
            fake.city(), fake.city(), random.choice(['Soltero(a)','Casado(a)','Divorciado(a)']),
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
        dob = fake.date_of_birth(minimum_age=1, maximum_age=90)
        edad = date.today().year - dob.year
        c.execute('INSERT OR IGNORE INTO Beneficiario VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (
            fake.bothify('B##??'), fake.name(), dob.isoformat(), fake.city(), edad,
            random.choice(['M','F','No Binario']), fake.job(), fake.job(), fake.bothify('CURP##########'),
            fake.bothify('SSS-####'), fake.company(), random.choice(['Sí','No']), fake.company(),
            random.choice(['Sí','No']), random.choice(['A','B','C']), fake.word()
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
            fake.bothify('REF##'), random.choice(['Web','Evento','Amigo']), random.choice(['Facebook','Instagram','TikTok']), fake.sentence()
        ))

    for _ in range(n_records):
        c.execute('INSERT OR IGNORE INTO Cirugia VALUES (?,?,?,?,?,?,?,?)', (
            fake.bothify('CIR##'), fake.bothify('NC-###'), fake.word(), fake.sentence(),
            random.choice(brands), fake.name(), fake.date_this_decade().isoformat(), fake.text(max_nb_chars=20)
        ))

    for _ in range(n_records):
        c.execute('INSERT OR IGNORE INTO Paciente VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (
            fake.bothify('P##??'), fake.name(), fake.bothify('EXP-#####'), random.choice(['Sí','No']),
            fake.company(), fake.state(), fake.city(), fake.name(), fake.name(), fake.name(), fake.company(), random.choice(['Sí','No'])
        ))

    tipos_donante = ['Individual','Grupo','Empresa']
    sectores_donante = ['Privado','Público','ONG']
    for _ in range(n_records):
        c.execute('INSERT OR IGNORE INTO Donantes VALUES (?,?,?,?,?,?,?,?,?)', (
            fake.bothify('D##??'), random.choice(tipos_donante), random.choice(sectores_donante), fake.name(),
            fake.phone_number(), fake.email(), fake.city(), fake.user_name(), fake.text()
            ))

    for _ in range(5):
        user = random.choice([u[0] for u in c.execute("SELECT id FROM Usuario").fetchall()])
        tipo = random.choice(["seguimiento","cita","cumpleaños","invitación"])
        msg  = f"Prueba de {tipo} para usuario {user}"
        due  = date.today().isoformat() + "T09:00:00"
        c.execute(
            "INSERT INTO Reminders(user_id, tipo, mensaje, due_datetime) VALUES (?,?,?,?)",
            (user, tipo, msg, due)
        )

    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_and_populate()