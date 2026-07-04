"""
SmartLearn — Plataforma Educativa Inteligente Offline
Python 3.11 + Kivy 2.3 · System Plus Piendamó · 2025
UI según mockup MJV APPIt

Ejecutar:  python main.py
Usuarios:  admin/admin123  |  docente/doc123  |  estudiante/est123
"""
import os, sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.checkbox import CheckBox
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line, Ellipse
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.lang import Builder

from database.db_manager import (
    init_db, login, get_contenidos, subir_contenido, registrar_descarga,
    get_evaluaciones, get_preguntas, guardar_resultado, get_resultados,
    crear_evaluacion, get_alertas_ambiente, atender_alerta_ambiente,
    registrar_alerta_ambiente, get_stats, get_usuarios, MODULOS
)
from sensors.sensor_emulator import SensorAmbiental

Window.size = (400, 720)
Builder.load_file(os.path.join(BASE_DIR, "smartlearn.kv"))

# ── Helpers de UI ──────────────────────────────────────────────
PURPLE     = (0.502, 0.302, 0.878, 1)
PURPLE_L   = (0.93,  0.88,  1.0,  1)
GOLD       = (0.788, 0.635, 0.153, 1)
WHITE      = (1, 1, 1, 1)
DARK       = (0.12, 0.08, 0.28, 1)
GRAY       = (0.55, 0.50, 0.65, 1)
GREEN      = (0.18, 0.65, 0.32, 1)
RED        = (0.80, 0.15, 0.15, 1)
ORANGE     = (0.90, 0.45, 0.0,  1)


def card(height=80, bg=WHITE, radius=14):
    w = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(4),
                  size_hint_y=None, height=dp(height))
    with w.canvas.before:
        Color(*bg)
        w._bg = RoundedRectangle(pos=w.pos, size=w.size, radius=[radius])
    w.bind(pos=lambda s, v: setattr(s._bg, 'pos', v),
           size=lambda s, v: setattr(s._bg, 'size', v))
    return w


def lbl(text, size=13, bold=False, color=DARK, halign='left', h=24, markup=False):
    l = Label(text=text, font_size=dp(size), bold=bold, color=color,
              size_hint_y=None, height=dp(h),
              halign=halign, text_size=(dp(370), None), markup=markup)
    return l


def purple_btn(text, callback, light=False, h=36):
    bg = PURPLE_L if light else PURPLE
    tc = PURPLE if light else WHITE
    b = Button(text=text, size_hint_y=None, height=dp(h),
               background_color=(0, 0, 0, 0), background_normal='',
               color=tc, font_size=dp(13))
    with b.canvas.before:
        Color(*bg)
        b._bg = RoundedRectangle(pos=b.pos, size=b.size, radius=[h // 2])
    b.bind(pos=lambda s, v: setattr(s._bg, 'pos', v),
           size=lambda s, v: setattr(s._bg, 'size', v),
           on_release=lambda _: callback())
    return b


def badge(text, bg_color):
    """Pequeño badge de color (Crítica / General / Emergencia)."""
    b = Label(text=text, font_size=dp(11), bold=True, color=WHITE,
              size_hint=(None, None), size=(dp(80), dp(22)))
    with b.canvas.before:
        Color(*bg_color)
        b._bg = RoundedRectangle(pos=b.pos, size=b.size, radius=[11])
    b.bind(pos=lambda s, v: setattr(s._bg, 'pos', v),
           size=lambda s, v: setattr(s._bg, 'size', v))
    return b


# ═══════════════════════════════════════════════════════════════
# LOGIN
# ═══════════════════════════════════════════════════════════════
class LoginScreen(Screen):
    def do_login(self):
        usuario  = self.ids.txt_usuario.text.strip()
        password = self.ids.txt_password.text.strip()
        if not usuario or not password:
            self.ids.lbl_error.text = "Completa todos los campos."
            return
        user = login(usuario, password)
        if user:
            App.get_running_app().current_user = user
            App.get_running_app().sensor.start()
            self.manager.transition = SlideTransition(direction='left')
            self.manager.current = 'dashboard'
        else:
            self.ids.lbl_error.text = "Usuario o contraseña incorrectos."
            self.ids.txt_password.text = ""


# ═══════════════════════════════════════════════════════════════
# DASHBOARD — construye contenido dinámico según rol
# ═══════════════════════════════════════════════════════════════
class DashboardScreen(Screen):
    _sensor_event = None

    def on_enter(self):
        app = App.get_running_app()
        u = app.current_user
        rol = u["rol"]

        self.ids.lbl_rol_header.text    = rol.capitalize()
        self.ids.lbl_nombre_header.text = "Mis Cursos" if rol == "estudiante" else (
            "MJV" if rol == "admin" else "Panel Docente")

        self._build_content(rol, u)
        self._sensor_event = Clock.schedule_interval(self._tick_sensors, 3)

    def on_leave(self):
        if self._sensor_event:
            self._sensor_event.cancel()

    # ── Constructor de contenido por rol ──────────────────────
    def _build_content(self, rol, user):
        content = self.ids.dash_content
        content.clear_widgets()
        if rol == "estudiante":
            self._build_estudiante(content, user)
        elif rol == "admin":
            self._build_admin(content)
        else:
            self._build_docente(content, user)

    def _build_estudiante(self, content, user):
        stats = get_stats()
        # Módulo activo
        content.add_widget(lbl("Aplicaciones Móviles", 22, bold=True, color=DARK, h=36))
        content.add_widget(lbl("Estudiante", 13, color=GRAY, h=22))

        # Barra de avance
        avance = min(stats["resultados"] * 15, 100)
        row_av = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(8))
        row_av.add_widget(lbl("Avance del módulo:", 13, color=GRAY, h=24))
        row_av.add_widget(lbl(f"{avance}%", 14, bold=True, color=PURPLE, h=24, halign='right'))
        content.add_widget(row_av)

        # Barra visual
        bar_bg = BoxLayout(size_hint_y=None, height=dp(8))
        with bar_bg.canvas.before:
            Color(0.88, 0.84, 0.96, 1)
            bar_bg._bg = RoundedRectangle(pos=bar_bg.pos, size=bar_bg.size, radius=[4])
        bar_bg.bind(pos=lambda s, v: setattr(s._bg, 'pos', v),
                    size=lambda s, v: setattr(s._bg, 'size', v))
        fill = BoxLayout(size_hint_x=avance / 100)
        with fill.canvas.before:
            Color(*PURPLE)
            fill._fg = RoundedRectangle(pos=fill.pos, size=fill.size, radius=[4])
        fill.bind(pos=lambda s, v: setattr(s._fg, 'pos', v),
                  size=lambda s, v: setattr(s._fg, 'size', v))
        bar_bg.add_widget(fill)
        bar_bg.add_widget(BoxLayout(size_hint_x=1 - avance / 100))
        content.add_widget(bar_bg)

        # Buscador / estado
        busq = BoxLayout(size_hint_y=None, height=dp(46), padding=dp(14, 0))
        with busq.canvas.before:
            Color(*WHITE)
            busq._bg = RoundedRectangle(pos=busq.pos, size=busq.size, radius=[23])
        busq.bind(pos=lambda s, v: setattr(s._bg, 'pos', v),
                  size=lambda s, v: setattr(s._bg, 'size', v))
        busq.add_widget(lbl(f"  Avance del módulo: {avance}%", 13, color=GRAY, h=46))
        busq.add_widget(lbl("🔍", 18, h=46, halign='right'))
        content.add_widget(busq)

        # Temas del módulo
        content.add_widget(lbl("Contenidos disponibles", 14, bold=True, color=DARK, h=32))
        contenidos = get_contenidos("Programación")[:3]
        for con in contenidos:
            c = card(50, WHITE)
            row = BoxLayout(spacing=dp(10))
            row.add_widget(lbl(con["titulo"], 14, bold=True, color=DARK, h=26))
            row.add_widget(lbl("›", 18, color=PURPLE, h=26, halign='right'))
            c.add_widget(row)
            content.add_widget(c)

        # Tarjeta RF-03 con acciones
        content.add_widget(lbl("Módulo destacado", 14, bold=True, color=DARK, h=32))
        rf_card = card(165, (0.655, 0.545, 0.980, 0.12), radius=14)
        rf_card.add_widget(lbl("RF-03", 18, bold=True, color=PURPLE, h=28))
        grid_rf = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(110))
        left = BoxLayout(orientation='vertical', spacing=dp(6))
        for txt in ["Teoría.pdf  ›", "Gráficas  ›", "Marcar offline  ›"]:
            left.add_widget(purple_btn(txt, lambda: None, light=True))
        right = BoxLayout(orientation='vertical', spacing=dp(6))
        right.add_widget(lbl("RF-03", 13, bold=True, color=PURPLE, h=24))
        right.add_widget(purple_btn("Ver online", lambda: None))
        right.add_widget(purple_btn("Marcar offline", lambda: None, light=True))
        grid_rf.add_widget(left)
        grid_rf.add_widget(right)
        rf_card.add_widget(grid_rf)
        content.add_widget(rf_card)

        content.add_widget(purple_btn("Intentar ahora", lambda: self.go_to('evaluaciones'), h=48))

    def _build_admin(self, content):
        stats = get_stats()
        content.add_widget(lbl("Panel Administrador", 14, color=GRAY, h=22))
        content.add_widget(lbl("System Plus Piendamo", 14, bold=True, color=DARK, h=28))

        # Grid de stats — mismo layout que el mockup
        grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(200))

        def stat_card(valor, etiqueta):
            c = card(90, WHITE, radius=16)
            c.add_widget(lbl(etiqueta, 13, color=GRAY, h=20))
            c.add_widget(lbl(str(valor), 30, bold=True, color=PURPLE, h=44))
            return c

        grid.add_widget(stat_card("1,240", "Total Usuarios:"))
        grid.add_widget(stat_card("42",    "Cursos\nActivos:"))
        grid.add_widget(stat_card("284",   "Estudiantes\nConectado: Hy:"))
        grid.add_widget(stat_card(str(stats["alertas"]), "Alertas\nactivas:"))
        content.add_widget(grid)

        # Botones de acción
        row_btns = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(42))
        row_btns.add_widget(purple_btn("Gestionar Usuarios", lambda: self.go_to('usuarios')))
        row_btns.add_widget(purple_btn("Entrenar IA", lambda: None))
        content.add_widget(row_btns)

        # Últimas consultas IA
        content.add_widget(lbl("Ultimas Consultas IA", 15, bold=True, color=DARK, h=32))
        encabezado = BoxLayout(size_hint_y=None, height=dp(28))
        encabezado.add_widget(lbl("Estudiante", 12, color=GRAY, h=28))
        encabezado.add_widget(lbl("Estado", 12, color=GRAY, h=28, halign='right'))
        content.add_widget(encabezado)

        filas = [
            ("Ultimas Consultas IA", "Estado"),
            ("Estudiante",           "Estado"),
            ("Pregunta",             "Estado"),
            ("Estado",               "Estado"),
        ]
        for nombre, est in filas:
            row = BoxLayout(size_hint_y=None, height=dp(38), padding=dp(4))
            with row.canvas.before:
                Color(*WHITE)
                row._bg = RoundedRectangle(pos=row.pos, size=row.size, radius=[8])
            row.bind(pos=lambda s, v: setattr(s._bg, 'pos', v),
                     size=lambda s, v: setattr(s._bg, 'size', v))
            row.add_widget(lbl(nombre, 13, color=DARK, h=30))
            row.add_widget(lbl(f"{est} ›", 12, color=GRAY, h=30, halign='right'))
            content.add_widget(row)

    def _build_docente(self, content, user):
        stats = get_stats()

        # Header con avatar grande
        head = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(14))
        avatar = Label(text="👨‍🏫", font_size=dp(34),
                       size_hint=(None, None), size=(dp(56), dp(56)))
        head.add_widget(avatar)
        head.add_widget(lbl("Panel Docente", 22, bold=True, color=DARK, h=56))
        content.add_widget(head)

        # Acciones rápidas — mockup muestra 4 botones con íconos
        content.add_widget(lbl("Mis Cursos  ›", 14, bold=False, color=DARK, h=40))

        grid_acc = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(100))

        def accion_card(icono, texto, callback):
            c = card(44, WHITE, radius=10)
            row = BoxLayout(spacing=dp(8))
            row.add_widget(lbl(icono, 18, h=36))
            row.add_widget(lbl(texto, 13, color=DARK, h=36))
            c.add_widget(row)
            c.bind(on_touch_down=lambda w, t: callback() if w.collide_point(*t.pos) else None)
            return c

        grid_acc.add_widget(accion_card("📺", "Crear Módulo",     lambda: self.go_to('contenidos')))
        grid_acc.add_widget(accion_card("✅", "Crear Módulo",     lambda: self.go_to('contenidos')))
        grid_acc.add_widget(accion_card("📄", "Subir PDF/Imagen", lambda: self.go_to('contenidos')))
        grid_acc.add_widget(purple_btn("Crear Cuestionario", lambda: self.go_to('evaluaciones')))
        content.add_widget(grid_acc)

        # Cluro modavios (lista de módulos con estado)
        content.add_widget(lbl("", 4, h=10))
        header_mod = BoxLayout(size_hint_y=None, height=dp(28))
        header_mod.add_widget(lbl("Cluro modavios", 14, bold=True, color=DARK, h=28))
        header_mod.add_widget(lbl("States", 12, color=GRAY, h=28, halign='right'))
        content.add_widget(header_mod)

        modulos_doc = get_contenidos()[:5]
        nombres_fallback = ["Liiar Triear Amiings", "Liiar Trincel", "Flex", "Liiar leeo", "Liiar Magel"]
        for i, titulo in enumerate(nombres_fallback):
            con_titulo = modulos_doc[i]["titulo"] if i < len(modulos_doc) else titulo
            row = BoxLayout(size_hint_y=None, height=dp(44), padding=dp(10, 6))
            with row.canvas.before:
                Color(*WHITE)
                row._bg = RoundedRectangle(pos=row.pos, size=row.size, radius=[10])
            row.bind(pos=lambda s, v: setattr(s._bg, 'pos', v),
                     size=lambda s, v: setattr(s._bg, 'size', v))
            row.add_widget(lbl("📄", 16, h=32))
            row.add_widget(lbl(con_titulo, 13, color=DARK, h=32))
            row.add_widget(lbl("∨", 16, color=GRAY, h=32, halign='right'))
            content.add_widget(row)

        # Stats finales
        stat_row = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(80))

        def mini_stat(val, label):
            c = card(70, WHITE, radius=14)
            c.add_widget(lbl(label, 11, color=GRAY, h=18))
            c.add_widget(lbl(val, 24, bold=True, color=PURPLE, h=34))
            return c

        stat_row.add_widget(mini_stat("32",  "Estudiantes inscritos:"))
        stat_row.add_widget(mini_stat(f"{min(stats['resultados']*5, 100)}%", "Avance promedio:"))
        content.add_widget(stat_row)

    # ── NavBar y sensores ──────────────────────────────────────
    def _tick_sensors(self, dt):
        pass  # sensores en AmbienteScreen

    def go_to(self, screen):
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = screen

    def do_logout(self):
        App.get_running_app().sensor.stop()
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'login'


# ═══════════════════════════════════════════════════════════════
# USUARIOS (admin)
# ═══════════════════════════════════════════════════════════════
class UsuariosScreen(Screen):
    def on_enter(self):
        lista = self.ids.lista_usuarios
        lista.clear_widgets()
        usuarios = get_usuarios()
        for u in usuarios:
            c = card(56, WHITE)
            row = BoxLayout(spacing=dp(10))
            emoji = {"admin": "🔑", "docente": "👨‍🏫", "estudiante": "🎓"}.get(u["rol"], "👤")
            row.add_widget(lbl(emoji, 22, h=36))
            info = BoxLayout(orientation='vertical', spacing=dp(2))
            info.add_widget(lbl(u["nombre"], 14, bold=True, color=DARK, h=22))
            info.add_widget(lbl(f"@{u['usuario']} · {u['rol']}", 12, color=GRAY, h=18))
            row.add_widget(info)
            estado_color = GREEN if u["activo"] else RED
            estado_txt = "Activo" if u["activo"] else "Inactivo"
            row.add_widget(badge(estado_txt, estado_color))
            c.add_widget(row)
            lista.add_widget(c)

    def go_back(self):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'dashboard'


# ═══════════════════════════════════════════════════════════════
# CONTENIDOS
# ═══════════════════════════════════════════════════════════════
class ContenidosScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        rol = app.current_user["rol"]
        self.ids.btn_subir.opacity  = 1 if rol in ("admin", "docente") else 0
        self.ids.btn_subir.disabled = rol not in ("admin", "docente")
        modulos_lista = ["Todos los módulos"] + MODULOS
        self.ids.spin_modulo.values = modulos_lista
        self._cargar()

    def _cargar(self, modulo=None):
        lista = self.ids.lista_contenidos
        lista.clear_widgets()
        filtro = None if not modulo or modulo == "Todos los módulos" else modulo
        contenidos = get_contenidos(filtro)
        if not contenidos:
            lista.add_widget(lbl("Sin contenidos disponibles.", 14, color=GRAY, h=44))
            return

        modulo_actual = None
        for con in contenidos:
            if con["modulo"] != modulo_actual:
                modulo_actual = con["modulo"]
                lista.add_widget(lbl(modulo_actual, 14, bold=True, color=PURPLE, h=32))

            c = card(72, WHITE)
            row = BoxLayout(spacing=dp(8))
            info = BoxLayout(orientation='vertical', spacing=dp(2))
            info.add_widget(lbl(con["titulo"], 14, bold=True, color=DARK, h=24))
            info.add_widget(lbl(con["descripcion"] or "", 12, color=GRAY, h=20))
            info.add_widget(lbl(f"Tipo: {con['tipo']}  ·  {con['fecha_subida'][:10]}", 11, color=GRAY, h=18))
            btn_dl = Button(text="⬇", size_hint=(None, None), size=(dp(44), dp(60)),
                            background_color=(0, 0, 0, 0), background_normal='',
                            color=PURPLE, font_size=dp(20))
            cid = con["id"]
            btn_dl.bind(on_release=lambda _, c=cid: self._descargar(c))
            row.add_widget(info)
            row.add_widget(btn_dl)
            c.add_widget(row)
            lista.add_widget(c)

    def filtrar(self, modulo):
        self._cargar(modulo)

    def _descargar(self, cid):
        app = App.get_running_app()
        registrar_descarga(cid, app.current_user["id"])
        p = Popup(title="Descarga simulada",
                  content=Label(text="✓ Contenido marcado como descargado\n(modo offline)"),
                  size_hint=(0.82, 0.28))
        p.open()
        self._cargar(self.ids.spin_modulo.text)

    def abrir_form_subir(self):
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(14))
        txt_titulo = TextInput(hint_text='Título', multiline=False, size_hint_y=None, height=dp(42))
        txt_desc   = TextInput(hint_text='Descripción', multiline=False, size_hint_y=None, height=dp(42))
        spin_mod   = Spinner(text=MODULOS[0], values=MODULOS, size_hint_y=None, height=dp(42))
        spin_tipo  = Spinner(text='pdf', values=['pdf', 'video', 'presentacion', 'ejercicio'],
                             size_hint_y=None, height=dp(42))
        popup = Popup(title='Subir Contenido', size_hint=(0.92, 0.70))

        def guardar(_):
            if not txt_titulo.text.strip():
                return
            app = App.get_running_app()
            subir_contenido(txt_titulo.text.strip(), txt_desc.text.strip(),
                            spin_mod.text, spin_tipo.text, app.current_user["id"])
            popup.dismiss()
            self._cargar()

        btn = Button(text='Publicar', size_hint_y=None, height=dp(44),
                     background_color=(*PURPLE[:3], 1))
        btn.bind(on_release=guardar)
        for w in [txt_titulo, txt_desc, spin_mod, spin_tipo, btn]:
            content.add_widget(w)
        popup.content = content
        popup.open()

    def go_back(self):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'dashboard'


# ═══════════════════════════════════════════════════════════════
# EVALUACIONES
# ═══════════════════════════════════════════════════════════════
class EvaluacionesScreen(Screen):
    def on_enter(self):
        self._cargar()

    def _cargar(self):
        lista = self.ids.lista_evaluaciones
        lista.clear_widgets()
        app = App.get_running_app()
        rol = app.current_user["rol"]

        if rol in ("admin", "docente"):
            lista.add_widget(purple_btn("+ Crear cuestionario", self._form_nueva, h=44))

        evaluaciones = get_evaluaciones()
        if not evaluaciones:
            lista.add_widget(lbl("Sin cuestionarios disponibles.", 14, color=GRAY, h=44))
            return

        for ev in evaluaciones:
            c = card(80, WHITE)
            row = BoxLayout(spacing=dp(10))
            info = BoxLayout(orientation='vertical', spacing=dp(4))
            info.add_widget(lbl(ev["titulo"], 15, bold=True, color=PURPLE, h=26))
            info.add_widget(lbl(f"Módulo: {ev['modulo']}  ·  {ev['fecha_creacion'][:10]}", 12, color=GRAY, h=20))
            eid, etitle = ev["id"], ev["titulo"]
            btn_ir = Button(text="Realizar ›", size_hint=(None, None), size=(dp(90), dp(60)),
                            background_color=(0, 0, 0, 0), background_normal='',
                            color=PURPLE, font_size=dp(13), bold=True)
            btn_ir.bind(on_release=lambda _, i=eid, t=etitle: self._ir_quiz(i, t))
            row.add_widget(info)
            row.add_widget(btn_ir)
            c.add_widget(row)
            lista.add_widget(c)

    def _ir_quiz(self, eval_id, titulo):
        app = App.get_running_app()
        app.quiz_eval_id     = eval_id
        app.quiz_eval_titulo = titulo
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'quiz'

    def _form_nueva(self):
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(14))
        txt_titulo = TextInput(hint_text='Título del cuestionario', multiline=False,
                               size_hint_y=None, height=dp(42))
        spin_mod   = Spinner(text=MODULOS[0], values=MODULOS, size_hint_y=None, height=dp(42))
        popup = Popup(title='Nuevo Cuestionario', size_hint=(0.92, 0.42))

        def crear(_):
            if not txt_titulo.text.strip():
                return
            app = App.get_running_app()
            preguntas_demo = [
                ("¿Qué es un algoritmo?",
                 "Un lenguaje de programación",
                 "Secuencia de pasos para resolver un problema",
                 "Un tipo de dato", "Una función matemática", "b"),
                ("¿Qué es una variable?",
                 "Un valor constante",
                 "Un espacio en memoria para guardar datos",
                 "Un operador lógico", "Un ciclo repetitivo", "b"),
            ]
            crear_evaluacion(txt_titulo.text.strip(), spin_mod.text,
                             app.current_user["id"], preguntas_demo)
            popup.dismiss()
            self._cargar()

        btn = Button(text='Crear', size_hint_y=None, height=dp(44),
                     background_color=(*PURPLE[:3], 1))
        btn.bind(on_release=crear)
        for w in [txt_titulo, spin_mod, btn]:
            content.add_widget(w)
        popup.content = content
        popup.open()

    def go_back(self):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'dashboard'


# ═══════════════════════════════════════════════════════════════
# QUIZ
# ═══════════════════════════════════════════════════════════════
class QuizScreen(Screen):
    _respuestas = {}
    _preguntas  = []

    def on_enter(self):
        app = App.get_running_app()
        self.ids.lbl_titulo_quiz.text = getattr(app, 'quiz_eval_titulo', 'Quiz')
        self._preguntas  = get_preguntas(app.quiz_eval_id)
        self._respuestas = {}
        self._construir()

    def _construir(self):
        content = self.ids.quiz_content
        content.clear_widgets()
        if not self._preguntas:
            content.add_widget(lbl("Sin preguntas.", 14, color=GRAY, h=44))
            return

        for idx, preg in enumerate(self._preguntas):
            c = card(210, WHITE)
            c.add_widget(lbl(f"P{idx+1}. {preg['enunciado']}", 14, bold=True, color=PURPLE, h=42))
            for key, texto in [("a", preg["opcion_a"]), ("b", preg["opcion_b"]),
                                ("c", preg["opcion_c"]), ("d", preg["opcion_d"])]:
                row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(8))
                chk = CheckBox(group=f"preg_{preg['id']}", size_hint_x=None, width=dp(30))
                k, pid = key, preg["id"]
                chk.bind(active=lambda w, val, k=k, p=pid:
                         self._sel(p, k) if val else None)
                row.add_widget(chk)
                row.add_widget(lbl(f"{key.upper()}. {texto}", 13, color=DARK, h=30))
                c.add_widget(row)
            content.add_widget(c)

        btn = Button(text="✓ Enviar respuestas",
                     size_hint_y=None, height=dp(50),
                     background_color=(*PURPLE[:3], 1),
                     background_normal='', color=WHITE,
                     font_size=dp(15), bold=True)
        btn.bind(on_release=lambda _: self._enviar())
        content.add_widget(btn)

    def _sel(self, pid, opcion):
        self._respuestas[pid] = opcion

    def _enviar(self):
        if len(self._respuestas) < len(self._preguntas):
            Popup(title="Atención",
                  content=Label(text="Responde todas las preguntas."),
                  size_hint=(0.8, 0.25)).open()
            return
        puntaje = sum(1 for p in self._preguntas
                      if self._respuestas.get(p["id"]) == p["respuesta_correcta"])
        total = len(self._preguntas)
        pct   = int(puntaje / total * 100)
        app   = App.get_running_app()
        guardar_resultado(app.quiz_eval_id, app.current_user["id"], puntaje, total)
        msg = f"Resultado: {puntaje}/{total} ({pct}%)\n{'✓ Aprobado' if pct >= 60 else '✗ No aprobado'}"
        Popup(title="Resultado", content=Label(text=msg, font_size=dp(16)),
              size_hint=(0.82, 0.32)).open()

    def go_back(self):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'evaluaciones'


# ═══════════════════════════════════════════════════════════════
# RESULTADOS
# ═══════════════════════════════════════════════════════════════
class ResultadosScreen(Screen):
    def on_enter(self):
        lista = self.ids.lista_resultados
        lista.clear_widgets()
        app = App.get_running_app()
        uid = app.current_user["id"] if app.current_user["rol"] == "estudiante" else None
        for r in get_resultados(uid):
            pct     = int(r["puntaje"] / r["total_preguntas"] * 100) if r["total_preguntas"] else 0
            aprobado= pct >= 60
            bg = (0.93, 1.0, 0.93, 1) if aprobado else (1.0, 0.93, 0.93, 1)
            c  = card(70, bg)
            c.add_widget(lbl(r["eval_titulo"], 14, bold=True, color=PURPLE, h=24))
            estado = "✓ Aprobado" if aprobado else "✗ No aprobado"
            c.add_widget(lbl(f"{estado}  ·  {r['puntaje']}/{r['total_preguntas']} ({pct}%)  ·  {r['fecha'][:10]}",
                             12, color=GREEN if aprobado else RED, h=20))
            if uid is None:
                c.add_widget(lbl(f"Alumno: {r['alumno']}  ·  {r['modulo']}", 11, color=GRAY, h=18))
            lista.add_widget(c)

    def go_back(self):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'dashboard'


# ═══════════════════════════════════════════════════════════════
# AMBIENTE AULA
# ═══════════════════════════════════════════════════════════════
class AmbienteScreen(Screen):
    _event = None

    def on_enter(self):
        self._event = Clock.schedule_interval(self._actualizar, 2.5)
        self._actualizar()

    def on_leave(self):
        if self._event:
            self._event.cancel()

    def _actualizar(self, dt=None):
        app = App.get_running_app()
        e   = app.sensor.get_estado()
        cnt = self.ids.ambiente_content
        cnt.clear_widgets()

        estado  = app.sensor.estado_aula()
        colores = {"optimo": GREEN, "alerta": ORANGE, "critico": RED}
        textos  = {"optimo": "● Aula en condiciones óptimas",
                   "alerta": "⚠ Condición de alerta detectada",
                   "critico": "🚨 Condición crítica"}
        cnt.add_widget(lbl(textos[estado], 16, bold=True, color=colores[estado], h=38))

        sensores = [
            ("💡 LDR — Iluminación",  f"{e['lux']:.0f} lux",       e["lux"] >= 300),
            ("🔊 KY-037 — Ruido",     f"{e['db']:.0f} dB",         e["db"] <= 50),
            ("👤 PIR — Presencia",    "Sí" if e["presencia"] else "No", True),
            ("📏 HC-SR04 — Distancia", f"{e['distancia_cm']:.0f} cm", e["distancia_cm"] >= 30),
        ]
        for titulo, valor, ok in sensores:
            bg = (0.93, 1.0, 0.93, 1) if ok else (1.0, 0.93, 0.9, 1)
            c  = card(72, bg)
            c.add_widget(lbl(titulo, 13, bold=True, color=PURPLE, h=22))
            c.add_widget(lbl(valor, 22, bold=True, color=DARK, h=30))
            c.add_widget(lbl("Normal" if ok else "⚠ Fuera de rango",
                             12, color=GREEN if ok else RED, h=18))
            cnt.add_widget(c)

        # Simuladores
        cnt.add_widget(lbl("Simular condiciones", 14, bold=True, color=DARK, h=30))
        row_sim = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(40))
        for txt, fn in [("Poca luz", lambda: app.sensor.simular_poca_luz()),
                        ("Ruido alto", lambda: app.sensor.simular_ruido_alto()),
                        ("Proximidad", lambda: app.sensor.simular_proximidad())]:
            b = Button(text=txt, size_hint_y=None, height=dp(38),
                       background_color=(*ORANGE[:3], 1), background_normal='',
                       color=WHITE, font_size=dp(12))
            b.bind(on_release=lambda _, f=fn: (f(), self._actualizar()))
            row_sim.add_widget(b)
        cnt.add_widget(row_sim)

        # Alertas recientes
        cnt.add_widget(lbl("Alertas recientes", 14, bold=True, color=DARK, h=30))
        alertas = get_alertas_ambiente(solo_activas=False)
        if not alertas:
            cnt.add_widget(lbl("Sin alertas.", 13, color=GRAY, h=32))
        for a in alertas[:6]:
            atendida = a["atendida"]
            row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8), padding=(0, dp(4)))
            row.add_widget(lbl(("✓ " if atendida else "⚠ ") + a["descripcion"],
                               12, color=GRAY if atendida else RED, h=36))
            if not atendida:
                aid = a["id"]
                btn = Button(text="Atender", size_hint=(None, None), size=(dp(80), dp(34)),
                             background_color=(*PURPLE[:3], 1), background_normal='',
                             color=WHITE, font_size=dp(11))
                btn.bind(on_release=lambda _, i=aid: (atender_alerta_ambiente(i), self._actualizar()))
                row.add_widget(btn)
            cnt.add_widget(row)

    def go_back(self):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'dashboard'


# ═══════════════════════════════════════════════════════════════
# APP PRINCIPAL
# ═══════════════════════════════════════════════════════════════
class SmartLearnApp(App):
    current_user     = None
    sensor: SensorAmbiental = None
    quiz_eval_id     = None
    quiz_eval_titulo = ""

    def build(self):
        self.title = "SmartLearn — MJV APPIt · System Plus Piendamó"
        init_db()
        self.sensor = SensorAmbiental(on_alert=self._on_alert)
        sm = ScreenManager()
        for sc in [LoginScreen(name='login'), DashboardScreen(name='dashboard'),
                   UsuariosScreen(name='usuarios'), ContenidosScreen(name='contenidos'),
                   EvaluacionesScreen(name='evaluaciones'), QuizScreen(name='quiz'),
                   ResultadosScreen(name='resultados'), AmbienteScreen(name='ambiente')]:
            sm.add_widget(sc)
        return sm

    def _on_alert(self, tipo, valor, descripcion):
        registrar_alerta_ambiente(tipo, valor, descripcion)


if __name__ == "__main__":
    SmartLearnApp().run()
