# SmartLearn — Plataforma Educativa Inteligente Offline
**System Plus Piendamó · 2025**
Docente: Yasley Mayerly Camilo

---

## Requisitos
- Python 3.11
- Kivy 2.3.x

## Instalación
```bash
pip install kivy==2.3.0
```

## Ejecución
```bash
cd smartlearn
python main.py
```

## Usuarios de prueba
| Usuario    | Contraseña | Rol        |
|------------|-----------|------------|
| admin      | admin123  | Admin      |
| docente    | doc123    | Docente    |
| estudiante | est123    | Estudiante |
| ana        | ana123    | Estudiante |
| luis       | luis123   | Estudiante |

## Estructura del proyecto
```
smartlearn/
├── main.py                   ← App principal + todas las pantallas
├── smartlearn.kv             ← Layouts y estilos
├── requirements.txt
├── database/
│   └── db_manager.py         ← SQLite: contenidos, evaluaciones, resultados
├── sensors/
│   └── sensor_emulator.py    ← Emulador PIR, LDR, KY-037, HC-SR04
└── assets/                   ← Recursos multimedia offline
```

## Pantallas disponibles
- **Login** — 3 roles con control de acceso
- **Dashboard** — panel ambiental en tiempo real + estadísticas
- **Contenidos** — repositorio filtrable por módulo, descarga offline
- **Evaluaciones** — lista de quizzes, creación por docentes
- **Quiz** — interfaz de preguntas opción múltiple con resultado
- **Mis Resultados** — historial con porcentaje y estado (aprobado/reprobado)
- **Ambiente Aula** — 4 sensores en tiempo real + alertas gestionables

## Sensores emulados
| Sensor  | Mide        | Umbral de alerta          |
|---------|-------------|---------------------------|
| LDR     | Iluminación | < 300 lux                 |
| KY-037  | Ruido       | > 50 dB                   |
| HC-SR04 | Distancia   | < 30 cm (seguridad equipos)|
| PIR     | Presencia   | Control automático de luz  |

## Módulos académicos incluidos
Informática Básica, Programación, Redes, Contabilidad, Fisioterapia,
Psicología, Inglés, Diseño Gráfico, Administración, Electricidad,
Mecánica, Salud Ocupacional, Gestión Ambiental.

## Próximos pasos
- [ ] Compilar APK con Buildozer
- [ ] Integrar ESP32 real (MicroPython)
- [ ] Sincronización automática cuando hay red
- [ ] Exportar resultados a CSV/PDF
- [ ] Soporte multimedia en contenidos (video, audio)
