# StreamProject 🚀

Script de automatización y gestión completa de Git en Python para simplificar el flujo de trabajo diario.

## 🛠️ Git Manager Automatizado (`git_manager.py`)

Un asistente completo para gestionar todas las operaciones de Git con un solo comando o mediante un menú interactivo visual.

### ✨ Características Principales

- ⚡ **Auto-Sync Completo**: Descarga cambios remotos (Smart Pull), añade todo (`git add -A`), crea commit y sube (`git push`) en un solo paso.
- 🚀 **Guardar y Subir Rápido (Quick Push)**: Detecta cambios, genera un mensaje con fecha y conteo de archivos automáticamente (o te permite escribir uno personalizado), configura el upstream si no existe y sube a GitHub.
- 📥 **Smart Pull**: Si tienes cambios locales sin guardar, los guarda en un `stash` temporal, descarga los cambios remotos y restaura tus cambios automáticamente sin perder nada.
- 🌿 **Gestión de Ramas**:
  - Crear nuevas ramas y cambiarte a ellas inmediatamente (opcionalmente publicarlas en GitHub de una vez).
  - Cambiar entre ramas con selección numérica rápida (sin tener que escribir el nombre).
  - Fusionar ramas (`git merge`) con confirmación y detección de conflictos.
  - Eliminar ramas locales y/o remotas.
- 📊 **Estado y Diff Visual**: Muestra el estado del repositorio formateado en colores con archivos modificados, nuevos, borrados y estado frente al remoto (`ahead`/`behind`).
- 📜 **Historial Gráfico**: Muestra los últimos commits en formato gráfico visual.
- 📦 **Stash Automatizado**: Guardar, listar, recuperar y limpiar cambios temporales.
- ⏪ **Deshacer Cambios Seguros**:
  - Deshacer el último commit sin perder tus archivos (`git reset --soft HEAD~1`).
  - Descartar todos los cambios no guardados si deseas reiniciar limpio.

---

### 💻 Modos de Uso

#### 1. Modo Menú Interactivo (Recomendado)
Simplemente ejecuta:
```bash
python git_manager.py
```
o en Windows:
```cmd
git_manager.bat
```
Aparecerá un menú interactivo con todas las opciones numeradas:
```text
============================================================
             🛠️   GIT MANAGER AUTOMATIZADO 🚀
============================================================
  Rama actual: [ main ]  |  Remoto: [ origin ]
  Estado:      Limpio [ahead 1]
------------------------------------------------------------
  [1]  ⚡ Auto-Sync Completo (Pull inteligente + Add + Commit + Push)
  [2]  🚀 Guardar y Subir Rápido (Add + Commit + Push)
  [3]  📥 Descargar cambios (Smart Pull con auto-stash)
  [4]  🌿 Crear nueva rama y cambiarte a ella
  [5]  🔀 Cambiar de rama (Menú interactivo)
  [6]  🤝 Fusionar rama (Merge a la rama actual)
  [7]  🗑️  Eliminar rama (Local / Remota)
  [8]  📊 Ver estado detallado y cambios
  [9]  📜 Ver historial de commits (Log gráfico)
  [10] 📦 Stash (Guardar/Recuperar cambios temporales)
  [11] ⏪ Deshacer último commit (manteniendo archivos)
  [12] 🧹 Descartar cambios sin guardar (Limpieza total)
  [0]  🚪 Salir
============================================================
```

#### 2. Modo Comandos Directos (Para terminal o scripts)
Puedes ejecutar tareas automáticas directamente pasando argumentos:

```bash
# Guardar y subir todo en un comando (pide mensaje o autogenera uno si presionas enter)
python git_manager.py push

# Guardar y subir con mensaje específico
python git_manager.py push -m "feat: nuevo componente de stream"

# Descargar cambios de forma inteligente (con auto-stash si hay cambios locales)
python git_manager.py pull

# Sincronización bidireccional completa (Pull + Add + Commit + Push)
python git_manager.py sync

# Crear una nueva rama y activarla automáticamente
python git_manager.py branch feature/mi-nueva-rama

# Crear una nueva rama y publicarla directamente en GitHub
python git_manager.py branch feature/video-player --push

# Cambiar de rama rápidamente
python git_manager.py switch main

# Ver estado detallado con colores
python git_manager.py status

# Ver historial visual de commits
python git_manager.py log
```
