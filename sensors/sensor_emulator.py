"""
SmartLearn — Emulador de Sensores IoT Ambientales
Simula: PIR (presencia), LDR (luz), KY-037 (sonido), HC-SR04 (ultrasonido)
System Plus Piendamó · 2025
"""
import random
import threading
import time


class SensorAmbiental:
    """Emula los 4 sensores ambientales del ESP32 de SmartLearn."""

    # Umbrales pedagógicos
    UMBRAL_LUX_MIN    = 300    # lux — mínimo para lectura
    UMBRAL_DB_CLASE   = 50     # dB  — máximo aceptable en clase
    UMBRAL_CM_EQUIPO  = 30     # cm  — distancia de seguridad a equipos

    def __init__(self, on_alert=None):
        self.on_alert = on_alert   # callback(tipo, valor, descripcion)
        self._running = False
        self._thread  = None

        self.estado = {
            "presencia":   False,   # PIR
            "lux":         500.0,   # LDR
            "db":          35.0,    # KY-037
            "distancia_cm": 80.0,   # HC-SR04
            "luz_on":      False,   # estado del relé de iluminación
        }

        # Para throttle de alertas (no spamear)
        self._ultima_alerta = {}

    # ── Control ───────────────────────────────────────────────────
    def start(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            self._update()
            self._check_alerts()
            time.sleep(2.5)

    # ── Simulación ────────────────────────────────────────────────
    def _update(self):
        # PIR: cambia ocasionalmente
        if random.random() < 0.1:
            self.estado["presencia"] = not self.estado["presencia"]

        # Control automático de luz según PIR
        if self.estado["presencia"] and not self.estado["luz_on"]:
            self.estado["luz_on"] = True
        elif not self.estado["presencia"] and self.estado["luz_on"]:
            if random.random() < 0.05:   # apaga después de un tiempo
                self.estado["luz_on"] = False

        # LDR: varía suavemente, picos de oscuridad ocasionales
        self.estado["lux"] += random.uniform(-15, 15)
        if random.random() < 0.05:
            self.estado["lux"] -= random.uniform(100, 250)   # simula nube o cortina
        self.estado["lux"] = max(50.0, min(1500.0, self.estado["lux"]))

        # KY-037: ruido normal con picos
        self.estado["db"] += random.uniform(-2, 2)
        if random.random() < 0.06:
            self.estado["db"] += random.uniform(15, 30)   # pico de ruido
        self.estado["db"] = max(20.0, min(90.0, self.estado["db"]))

        # HC-SR04: distancia varía (alguien se acerca/aleja del equipo)
        self.estado["distancia_cm"] += random.uniform(-5, 5)
        if random.random() < 0.04:
            self.estado["distancia_cm"] = random.uniform(10, 25)   # acercamiento
        self.estado["distancia_cm"] = max(2.0, min(200.0, self.estado["distancia_cm"]))

    def _check_alerts(self):
        ahora = time.time()

        def puede_alertar(key, cooldown=20):
            ultima = self._ultima_alerta.get(key, 0)
            if ahora - ultima > cooldown:
                self._ultima_alerta[key] = ahora
                return True
            return False

        if self.estado["lux"] < self.UMBRAL_LUX_MIN and puede_alertar("lux") and self.on_alert:
            self.on_alert("lux", round(self.estado["lux"], 1),
                          f"💡 Iluminación insuficiente: {round(self.estado['lux'],1)} lux (mín. {self.UMBRAL_LUX_MIN})")

        if self.estado["db"] > self.UMBRAL_DB_CLASE and puede_alertar("ruido") and self.on_alert:
            self.on_alert("ruido", round(self.estado["db"], 1),
                          f"🔊 Nivel de ruido alto: {round(self.estado['db'],1)} dB (máx. {self.UMBRAL_DB_CLASE})")

        if self.estado["distancia_cm"] < self.UMBRAL_CM_EQUIPO and puede_alertar("proximidad") and self.on_alert:
            self.on_alert("proximidad", round(self.estado["distancia_cm"], 1),
                          f"⚠ Objeto cerca de equipo: {round(self.estado['distancia_cm'],1)} cm")

    # ── API ───────────────────────────────────────────────────────
    def get_estado(self):
        return dict(self.estado)

    def simular_poca_luz(self):
        self.estado["lux"] = 80.0
        self._check_alerts()

    def simular_ruido_alto(self):
        self.estado["db"] = 72.0
        self._check_alerts()

    def simular_proximidad(self):
        self.estado["distancia_cm"] = 15.0
        self._check_alerts()

    def simular_entrada_persona(self):
        self.estado["presencia"] = True
        self.estado["luz_on"] = True

    def get_lux(self):
        return round(self.estado["lux"], 1)

    def get_db(self):
        return round(self.estado["db"], 1)

    def get_distancia(self):
        return round(self.estado["distancia_cm"], 1)

    def hay_presencia(self):
        return self.estado["presencia"]

    def luz_encendida(self):
        return self.estado["luz_on"]

    def estado_aula(self):
        """Retorna 'optimo', 'alerta' o 'critico' según condiciones."""
        problemas = 0
        if self.estado["lux"] < self.UMBRAL_LUX_MIN:
            problemas += 1
        if self.estado["db"] > self.UMBRAL_DB_CLASE:
            problemas += 1
        if self.estado["distancia_cm"] < self.UMBRAL_CM_EQUIPO:
            problemas += 2
        if problemas == 0:
            return "optimo"
        elif problemas == 1:
            return "alerta"
        else:
            return "critico"
