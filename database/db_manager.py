"""
SmartLearn — Gestor de Base de Datos SQLite
Plataforma Educativa Inteligente Offline
System Plus Piendamó · 2025
"""
import sqlite3
import os
import hashlib
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "smartlearn.db")

MODULOS = [
    "Informática Básica", "Programación", "Redes", "Contabilidad",
    "Fisioterapia", "Psicología", "Inglés", "Diseño Gráfico",
    "Administración", "Electricidad", "Mecánica", "Salud Ocupacional",
    "Gestión Ambiental"
]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL CHECK(rol IN ('admin','docente','estudiante')),
            activo INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS contenidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descripcion TEXT,
            modulo TEXT NOT NULL,
            tipo TEXT DEFAULT 'pdf',
            ruta_archivo TEXT,
            autor_id INTEGER,
            fecha_subida TEXT NOT NULL,
            FOREIGN KEY(autor_id) REFERENCES usuarios(id)
        );

        CREATE TABLE IF NOT EXISTS descargas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contenido_id INTEGER NOT NULL,
            usuario_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            FOREIGN KEY(contenido_id) REFERENCES contenidos(id),
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        );

        CREATE TABLE IF NOT EXISTS evaluaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            modulo TEXT NOT NULL,
            autor_id INTEGER,
            fecha_creacion TEXT NOT NULL,
            FOREIGN KEY(autor_id) REFERENCES usuarios(id)
        );

        CREATE TABLE IF NOT EXISTS preguntas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evaluacion_id INTEGER NOT NULL,
            enunciado TEXT NOT NULL,
            opcion_a TEXT NOT NULL,
            opcion_b TEXT NOT NULL,
            opcion_c TEXT NOT NULL,
            opcion_d TEXT NOT NULL,
            respuesta_correcta TEXT NOT NULL,
            FOREIGN KEY(evaluacion_id) REFERENCES evaluaciones(id)
        );

        CREATE TABLE IF NOT EXISTS resultados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evaluacion_id INTEGER NOT NULL,
            usuario_id INTEGER NOT NULL,
            puntaje INTEGER,
            total_preguntas INTEGER,
            fecha TEXT NOT NULL,
            sincronizado INTEGER DEFAULT 0,
            FOREIGN KEY(evaluacion_id) REFERENCES evaluaciones(id),
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        );

        CREATE TABLE IF NOT EXISTS alertas_ambiente (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            valor REAL,
            descripcion TEXT,
            fecha TEXT NOT NULL,
            atendida INTEGER DEFAULT 0
        );
    """)

    def hp(pw):
        return hashlib.sha256(pw.encode()).hexdigest()

    for u in [
        ("Administrador", "admin",    hp("admin123"), "admin"),
        ("Docente Demo",  "docente",  hp("doc123"),   "docente"),
        ("Estudiante Demo","estudiante", hp("est123"), "estudiante"),
        ("Ana Torres",    "ana",      hp("ana123"),   "estudiante"),
        ("Luis Muñoz",    "luis",     hp("luis123"),  "estudiante"),
    ]:
        try:
            c.execute("INSERT INTO usuarios (nombre,usuario,password,rol) VALUES (?,?,?,?)", u)
        except sqlite3.IntegrityError:
            pass

    # Seed contenidos
    contenidos_seed = [
        ("Introducción a Python", "Variables, tipos de datos y estructuras básicas", "Programación", "pdf", 2),
        ("Fundamentos de Redes", "Modelo OSI, protocolos TCP/IP", "Redes", "pdf", 2),
        ("Excel Básico", "Fórmulas y tablas dinámicas para contabilidad", "Contabilidad", "pdf", 2),
        ("Anatomía Básica", "Sistemas del cuerpo humano", "Fisioterapia", "pdf", 2),
        ("Python: Funciones", "Funciones, módulos y excepciones", "Programación", "pdf", 2),
    ]
    for con in contenidos_seed:
        try:
            c.execute(
                "INSERT INTO contenidos (titulo,descripcion,modulo,tipo,autor_id,fecha_subida) VALUES (?,?,?,?,?,?)",
                (*con, datetime.now().isoformat())
            )
        except Exception:
            pass

    # Seed evaluaciones
    now = datetime.now().isoformat()
    try:
        c.execute("INSERT INTO evaluaciones (titulo,modulo,autor_id,fecha_creacion) VALUES (?,?,?,?)",
                  ("Quiz: Python Básico", "Programación", 2, now))
        eval_id = c.lastrowid
        preguntas = [
            ("¿Qué función imprime en Python?", "echo()", "print()", "console.log()", "write()", "b"),
            ("¿Cuál es el tipo de dato de '3.14'?", "int", "str", "float", "bool", "c"),
            ("¿Cómo se define una lista?", "{1,2,3}", "[1,2,3]", "(1,2,3)", "<1,2,3>", "b"),
            ("¿Qué hace range(5)?", "Genera 1 al 5", "Genera 0 al 4", "Genera 0 al 5", "Genera 1 al 4", "b"),
            ("Indentación en Python usa:", "Llaves {}", "Paréntesis ()", "Espacios/Tabs", "Corchetes []", "c"),
        ]
        for p in preguntas:
            c.execute(
                "INSERT INTO preguntas (evaluacion_id,enunciado,opcion_a,opcion_b,opcion_c,opcion_d,respuesta_correcta) VALUES (?,?,?,?,?,?,?)",
                (eval_id, *p)
            )
    except Exception:
        pass

    conn.commit()
    conn.close()


# ── Usuarios ───────────────────────────────────────────────────
def login(usuario, password):
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM usuarios WHERE usuario=? AND password=? AND activo=1",
        (usuario, pw_hash)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Contenidos ─────────────────────────────────────────────────
def get_contenidos(modulo=None):
    conn = get_connection()
    if modulo:
        rows = conn.execute(
            "SELECT c.*,u.nombre AS autor FROM contenidos c "
            "LEFT JOIN usuarios u ON c.autor_id=u.id WHERE c.modulo=? ORDER BY c.fecha_subida DESC",
            (modulo,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT c.*,u.nombre AS autor FROM contenidos c "
            "LEFT JOIN usuarios u ON c.autor_id=u.id ORDER BY c.modulo,c.titulo"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def subir_contenido(titulo, descripcion, modulo, tipo, autor_id, ruta=""):
    conn = get_connection()
    conn.execute(
        "INSERT INTO contenidos (titulo,descripcion,modulo,tipo,autor_id,ruta_archivo,fecha_subida) VALUES (?,?,?,?,?,?,?)",
        (titulo, descripcion, modulo, tipo, autor_id, ruta, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def registrar_descarga(contenido_id, usuario_id):
    conn = get_connection()
    conn.execute(
        "INSERT INTO descargas (contenido_id,usuario_id,fecha) VALUES (?,?,?)",
        (contenido_id, usuario_id, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_descargas_por_contenido():
    conn = get_connection()
    rows = conn.execute(
        "SELECT c.titulo, c.modulo, COUNT(d.id) AS total "
        "FROM contenidos c LEFT JOIN descargas d ON c.id=d.contenido_id "
        "GROUP BY c.id ORDER BY total DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Evaluaciones ───────────────────────────────────────────────
def get_evaluaciones(modulo=None):
    conn = get_connection()
    q = "SELECT e.*,u.nombre AS autor FROM evaluaciones e LEFT JOIN usuarios u ON e.autor_id=u.id"
    params = ()
    if modulo:
        q += " WHERE e.modulo=?"
        params = (modulo,)
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_preguntas(evaluacion_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM preguntas WHERE evaluacion_id=?", (evaluacion_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def guardar_resultado(evaluacion_id, usuario_id, puntaje, total):
    conn = get_connection()
    conn.execute(
        "INSERT INTO resultados (evaluacion_id,usuario_id,puntaje,total_preguntas,fecha) VALUES (?,?,?,?,?)",
        (evaluacion_id, usuario_id, puntaje, total, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_resultados(usuario_id=None):
    conn = get_connection()
    q = ("SELECT r.*,e.titulo AS eval_titulo,e.modulo,u.nombre AS alumno "
         "FROM resultados r "
         "JOIN evaluaciones e ON r.evaluacion_id=e.id "
         "JOIN usuarios u ON r.usuario_id=u.id")
    params = ()
    if usuario_id:
        q += " WHERE r.usuario_id=?"
        params = (usuario_id,)
    q += " ORDER BY r.fecha DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def crear_evaluacion(titulo, modulo, autor_id, preguntas):
    """preguntas = list of (enunciado, a, b, c, d, respuesta_correcta)"""
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO evaluaciones (titulo,modulo,autor_id,fecha_creacion) VALUES (?,?,?,?)",
        (titulo, modulo, autor_id, datetime.now().isoformat())
    )
    eid = c.lastrowid
    for p in preguntas:
        c.execute(
            "INSERT INTO preguntas (evaluacion_id,enunciado,opcion_a,opcion_b,opcion_c,opcion_d,respuesta_correcta) VALUES (?,?,?,?,?,?,?)",
            (eid, *p)
        )
    conn.commit()
    conn.close()
    return eid


# ── Alertas Ambiente ───────────────────────────────────────────
def registrar_alerta_ambiente(tipo, valor, descripcion):
    conn = get_connection()
    conn.execute(
        "INSERT INTO alertas_ambiente (tipo,valor,descripcion,fecha) VALUES (?,?,?,?)",
        (tipo, valor, descripcion, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_alertas_ambiente(solo_activas=True):
    conn = get_connection()
    q = "SELECT * FROM alertas_ambiente"
    if solo_activas:
        q += " WHERE atendida=0"
    q += " ORDER BY fecha DESC LIMIT 50"
    rows = conn.execute(q).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def atender_alerta_ambiente(alerta_id):
    conn = get_connection()
    conn.execute("UPDATE alertas_ambiente SET atendida=1 WHERE id=?", (alerta_id,))
    conn.commit()
    conn.close()


# ── Stats Dashboard ────────────────────────────────────────────
def get_stats():
    conn = get_connection()
    s = {}
    s["contenidos"]  = conn.execute("SELECT COUNT(*) FROM contenidos").fetchone()[0]
    s["evaluaciones"] = conn.execute("SELECT COUNT(*) FROM evaluaciones").fetchone()[0]
    s["descargas"]   = conn.execute("SELECT COUNT(*) FROM descargas").fetchone()[0]
    s["resultados"]  = conn.execute("SELECT COUNT(*) FROM resultados").fetchone()[0]
    s["alertas"]     = conn.execute("SELECT COUNT(*) FROM alertas_ambiente WHERE atendida=0").fetchone()[0]
    conn.close()
    return s


def get_usuarios():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, nombre, usuario, rol, activo FROM usuarios"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
