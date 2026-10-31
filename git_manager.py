#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git Manager Automatizado
Script interactivo y de línea de comandos para automatizar y simplificar el flujo de trabajo con Git.
"""

import sys
import os
import subprocess
import argparse
from datetime import datetime

# Configurar codificación UTF-8 en consola de Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
    os.system('') # Habilita secuencias de escape ANSI VT100 en Windows 10/11

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'
    GRAY = '\033[90m'

def print_header(title):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}   {title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}\n")

def print_success(msg):
    print(f"{Colors.GREEN}[OK] {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.CYAN}[INFO] {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}[AVISO] {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}[ERROR] {msg}{Colors.RESET}")

def run_git(args, capture=True, check=False, silent=False):
    """Ejecuta un comando git y retorna stdout, stderr y el código de salida."""
    cmd = ["git"] + args
    try:
        if capture:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            # Preservar espacios iniciales en stdout usando rstrip
            stdout = res.stdout.rstrip("\r\n")
            stderr = res.stderr.rstrip("\r\n")
            if check and res.returncode != 0:
                if not silent:
                    print_error(f"Error al ejecutar {' '.join(cmd)}:\n{stderr}")
            return stdout, stderr, res.returncode
        else:
            code = subprocess.call(cmd)
            return "", "", code
    except FileNotFoundError:
        print_error("Git no está instalado o no se encuentra en el PATH del sistema.")
        sys.exit(1)
    except Exception as e:
        if not silent:
            print_error(f"Excepción al ejecutar git: {e}")
        return "", str(e), 1

def is_git_repo():
    _, _, code = run_git(["rev-parse", "--is-inside-work-tree"], capture=True, silent=True)
    return code == 0

def get_current_branch():
    out, _, code = run_git(["branch", "--show-current"])
    if code == 0 and out:
        return out
    out, _, code = run_git(["rev-parse", "--short", "HEAD"], silent=True)
    return out if code == 0 else "desconocida"

def get_remote_name():
    out, _, code = run_git(["remote"])
    if code == 0 and out:
        return out.splitlines()[0]
    return "origin"

def has_upstream():
    out, _, code = run_git(["rev-parse", "--abbrev-ref", "@{u}"], silent=True)
    return code == 0 and bool(out)

def get_changes_summary():
    out, _, _ = run_git(["status", "--porcelain"])
    if not out:
        return []
    return out.splitlines()

def get_ahead_behind():
    out, _, code = run_git(["status", "-sb"], silent=True)
    if code != 0 or not out:
        return ""
    first_line = out.splitlines()[0]
    if "[" in first_line and "]" in first_line:
        return first_line[first_line.find("["):first_line.find("]")+1]
    return ""

def parse_porcelain_line(c):
    if len(c) < 3:
        return c, ""
    status_code = c[:2]
    filename = c[3:].strip()
    return status_code, filename

# ==================== ACCIONES AUTOMATIZADAS ====================

def cmd_status():
    """Muestra el estado actual formateado y detallado."""
    print_header("ESTADO DEL REPOSITORIO")
    if not is_git_repo():
        print_error("Este directorio no es un repositorio Git.")
        return

    branch = get_current_branch()
    remote = get_remote_name()
    ahead = get_ahead_behind()
    changes = get_changes_summary()

    print(f"{Colors.BOLD}Rama actual:{Colors.RESET} {Colors.GREEN}{branch}{Colors.RESET} {Colors.YELLOW}{ahead}{Colors.RESET}")
    print(f"{Colors.BOLD}Remoto:{Colors.RESET}      {Colors.CYAN}{remote}{Colors.RESET}")

    if not changes:
        print_success("Árbol de trabajo limpio (sin cambios pendientes).")
    else:
        print(f"\n{Colors.BOLD}Cambios detectados ({len(changes)} archivo(s)):{Colors.RESET}")
        for c in changes:
            status_code, filename = parse_porcelain_line(c)
            if status_code.startswith("?") or status_code.endswith("?"):
                print(f"  {Colors.YELLOW}[Nuevo/Sin seguimiento] {filename}{Colors.RESET}")
            elif "M" in status_code:
                print(f"  {Colors.CYAN}[Modificado]            {filename}{Colors.RESET}")
            elif "D" in status_code:
                print(f"  {Colors.RED}[Eliminado]             {filename}{Colors.RESET}")
            elif "A" in status_code:
                print(f"  {Colors.GREEN}[Agregado al commit]    {filename}{Colors.RESET}")
            elif "R" in status_code:
                print(f"  {Colors.BLUE}[Renombrado]            {filename}{Colors.RESET}")
            else:
                print(f"  [{status_code}] {filename}")

def cmd_quick_push(message=None):
    """Agrega todos los cambios, hace commit y push automáticamente."""
    print_header("GUARDAR Y SUBIR AUTOMÁTICAMENTE (ADD + COMMIT + PUSH)")
    if not is_git_repo():
        print_error("No es un repositorio Git.")
        return False

    changes = get_changes_summary()
    branch = get_current_branch()
    remote = get_remote_name()

    if not changes:
        print_info("No hay archivos modificados o nuevos para commitear.")
        # Verificar si hay commits pendientes de subir
        ahead = get_ahead_behind()
        if "ahead" in ahead:
            print_info(f"Tienes commits locales listos para subir ({ahead}). Subiendo...")
            return push_to_remote(branch, remote)
        print_success("Todo está al día con el servidor.")
        return True

    print_info(f"Se detectaron {len(changes)} archivo(s) para guardar.")
    
    # 1. git add -A
    run_git(["add", "-A"], check=True)
    print_success("Archivos agregados al área de preparación (git add -A).")

    # 2. Determinar mensaje de commit
    if not message or not message.strip():
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        default_msg = f"Auto-update: {now_str} ({len(changes)} archivos)"
        resp = input(f"{Colors.YELLOW}Mensaje de commit [{default_msg}]: {Colors.RESET}").strip()
        message = resp if resp else default_msg

    # 3. git commit
    out, err, code = run_git(["commit", "-m", message])
    if code != 0:
        print_error(f"Error al commitear:\n{err}")
        return False
    print_success(f"Commit realizado con éxito: '{message}'")

    # 4. git push
    return push_to_remote(branch, remote)

def push_to_remote(branch, remote):
    print_info(f"Subiendo cambios a {remote}/{branch}...")
    if not has_upstream():
        print_info(f"Configurando rama remota de seguimiento (-u {remote} {branch})...")
        _, err, code = run_git(["push", "-u", remote, branch], capture=False)
    else:
        _, err, code = run_git(["push", remote, branch], capture=False)

    if code == 0:
        print_success("¡Cambios subidos a GitHub/remoto exitosamente!")
        return True
    else:
        print_error("Error al subir cambios (push). Verifica tus credenciales o conexión de red.")
        return False

def cmd_smart_pull():
    """Descarga cambios (pull) con manejo inteligente de cambios locales (auto-stash)."""
    print_header("DESCARGAR CAMBIOS INTELIGENTE (SMART PULL)")
    if not is_git_repo():
        print_error("No es un repositorio Git.")
        return False

    branch = get_current_branch()
    remote = get_remote_name()
    changes = get_changes_summary()
    stashed = False

    if changes:
        print_warning("Tienes cambios locales sin commitear. Guardando en stash temporalmente...")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        run_git(["stash", "push", "-u", "-m", f"Auto-stash antes de pull: {now_str}"], check=True)
        stashed = True
        print_success("Cambios locales resguardados en stash temporal.")

    print_info(f"Descargando actualizaciones de {remote}/{branch}...")
    out, err, code = run_git(["pull", remote, branch])

    if code == 0:
        print_success(f"Pull completado exitosamente.\n{out}")
    else:
        print_error(f"Error durante el pull:\n{err}")

    if stashed:
        print_info("Restaurando tus cambios locales desde el stash...")
        out_pop, err_pop, code_pop = run_git(["stash", "pop"])
        if code_pop == 0:
            print_success("Cambios locales restaurados sin conflictos.")
        else:
            print_warning("Hubo conflictos al restaurar los cambios del stash. Revisa tus archivos.")

    return code == 0

def cmd_full_auto_sync(message=None):
    """Flujo completo automatizado: Smart Pull + Add + Commit + Push."""
    print_header("AUTO-SYNC COMPLETO (PULL + COMMIT + PUSH)")
    print_info("Paso 1: Descargando cambios remotos...")
    pull_ok = cmd_smart_pull()
    if not pull_ok:
        cont = input(f"{Colors.YELLOW}El pull tuvo advertencias. ¿Deseas continuar con el guardado y push? (s/n): {Colors.RESET}").lower()
        if cont not in ['s', 'si', 'y', 'yes']:
            print_info("Operación cancelada.")
            return False

    print_info("\nPaso 2: Guardando y subiendo tus cambios...")
    return cmd_quick_push(message=message)

def get_all_branches():
    out, _, _ = run_git(["branch", "-a"])
    branches = []
    current = get_current_branch()
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        is_curr = line.startswith("*")
        b_name = line.replace("*", "").strip()
        if "->" in b_name:
            continue
        branches.append({"name": b_name, "current": is_curr})
    return branches, current

def cmd_create_branch(branch_name=None, checkout=True, push_upstream=False):
    """Crea una nueva rama y opcionalmente se cambia a ella."""
    print_header("CREAR NUEVA RAMA")
    if not is_git_repo():
        print_error("No es un repositorio Git.")
        return

    if not branch_name:
        branch_name = input(f"{Colors.YELLOW}Nombre de la nueva rama (ej. feature/login): {Colors.RESET}").strip()
    if not branch_name:
        print_error("El nombre de la rama no puede estar vacío.")
        return

    # Limpiar espacios
    branch_name = branch_name.replace(" ", "-")

    if checkout:
        out, err, code = run_git(["checkout", "-b", branch_name])
    else:
        out, err, code = run_git(["branch", branch_name])

    if code == 0:
        print_success(f"Rama '{branch_name}' creada exitosamente" + (" y activada." if checkout else "."))
        if push_upstream:
            remote = get_remote_name()
            print_info(f"Publicando rama en remoto {remote}...")
            run_git(["push", "-u", remote, branch_name], capture=False)
    else:
        print_error(f"Error al crear rama:\n{err}")

def cmd_switch_branch(branch_name=None):
    """Cambia a otra rama de forma interactiva con menú numerado."""
    print_header("CAMBIAR DE RAMA")
    if not is_git_repo():
        print_error("No es un repositorio Git.")
        return

    out, _, _ = run_git(["branch", "--list"])
    local_branches = [b.replace("*", "").strip() for b in out.splitlines() if b.strip()]
    curr = get_current_branch()

    if branch_name:
        out, err, code = run_git(["checkout", branch_name])
        if code == 0:
            print_success(f"Cambiado a la rama '{branch_name}'.")
        else:
            print_error(f"Error al cambiar a la rama '{branch_name}':\n{err}")
        return

    if not local_branches:
        print_warning("No hay ramas disponibles.")
        return

    print("Ramas locales disponibles:")
    for idx, b in enumerate(local_branches, 1):
        marker = f"{Colors.GREEN}* (Actual){Colors.RESET}" if b == curr else ""
        print(f"  [{idx}] {b} {marker}")

    choice = input(f"\n{Colors.YELLOW}Selecciona el número de la rama a la que deseas cambiar (o 0 para cancelar): {Colors.RESET}").strip()
    if not choice or choice == "0":
        return

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(local_branches):
            target = local_branches[idx]
            if target == curr:
                print_info(f"Ya estás en la rama '{target}'.")
                return
            out, err, code = run_git(["checkout", target])
            if code == 0:
                print_success(f"Cambiado a la rama '{target}'.")
            else:
                print_error(f"Error al cambiar de rama:\n{err}")
        else:
            print_error("Opción inválida.")
    except ValueError:
        print_error("Por favor ingresa un número válido.")

def cmd_merge_branch(branch_name=None):
    """Fusiona una rama seleccionada dentro de la rama actual."""
    print_header("FUSIONAR RAMA (MERGE)")
    curr = get_current_branch()
    print_info(f"Rama destino actual: {Colors.GREEN}{curr}{Colors.RESET}")

    out, _, _ = run_git(["branch", "--list"])
    local_branches = [b.replace("*", "").strip() for b in out.splitlines() if b.replace("*", "").strip() != curr]

    if not branch_name:
        if not local_branches:
            print_warning("No hay otras ramas locales para fusionar.")
            return

        print("Ramas disponibles para fusionar en la actual:")
        for idx, b in enumerate(local_branches, 1):
            print(f"  [{idx}] {b}")

        choice = input(f"\n{Colors.YELLOW}Número de la rama a fusionar (o 0 para cancelar): {Colors.RESET}").strip()
        if not choice or choice == "0":
            return
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(local_branches):
                branch_name = local_branches[idx]
            else:
                print_error("Número fuera de rango.")
                return
        except ValueError:
            print_error("Entrada no válida.")
            return

    confirm = input(f"{Colors.YELLOW}¿Seguro de fusionar '{branch_name}' dentro de '{curr}'? (s/n): {Colors.RESET}").lower()
    if confirm in ['s', 'si', 'y', 'yes']:
        out, err, code = run_git(["merge", branch_name])
        if code == 0:
            print_success(f"Fusión completada con éxito:\n{out}")
        else:
            print_error(f"Hubo conflictos o error en el merge:\n{err}\n{out}")

def cmd_delete_branch(branch_name=None):
    """Elimina una rama local y/o remota."""
    print_header("ELIMINAR RAMA")
    curr = get_current_branch()
    out, _, _ = run_git(["branch", "--list"])
    local_branches = [b.replace("*", "").strip() for b in out.splitlines() if b.replace("*", "").strip() != curr]

    if not branch_name:
        if not local_branches:
            print_warning("No hay ramas disponibles para eliminar.")
            return
        print("Ramas locales disponibles para eliminar:")
        for idx, b in enumerate(local_branches, 1):
            print(f"  [{idx}] {b}")

        choice = input(f"\n{Colors.YELLOW}Número de la rama a eliminar (o 0 para cancelar): {Colors.RESET}").strip()
        if not choice or choice == "0":
            return
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(local_branches):
                branch_name = local_branches[idx]
            else:
                print_error("Opción fuera de rango.")
                return
        except ValueError:
            print_error("Número no válido.")
            return

    confirm = input(f"{Colors.RED}¿Confirmas eliminar la rama local '{branch_name}'? (s/n): {Colors.RESET}").lower()
    if confirm in ['s', 'si', 'y', 'yes']:
        out, err, code = run_git(["branch", "-d", branch_name])
        if code != 0:
            force = input(f"{Colors.YELLOW}La rama no está totalmente fusionada. ¿Forzar borrado (-D)? (s/n): {Colors.RESET}").lower()
            if force in ['s', 'si', 'y', 'yes']:
                run_git(["branch", "-D", branch_name], capture=False)
        else:
            print_success(f"Rama local '{branch_name}' eliminada.")

        del_remote = input(f"{Colors.YELLOW}¿Deseas eliminarla también del remoto (GitHub)? (s/n): {Colors.RESET}").lower()
        if del_remote in ['s', 'si', 'y', 'yes']:
            remote = get_remote_name()
            run_git(["push", remote, "--delete", branch_name], capture=False)

def cmd_stash_menu():
    """Menú para guardar, listar y aplicar stashes."""
    print_header("GESTIÓN DE STASH (CAMBIOS TEMPORALES)")
    print("  [1] Guardar cambios actuales en stash")
    print("  [2] Recuperar último stash (pop)")
    print("  [3] Ver lista de stashes")
    print("  [4] Borrar todos los stashes (clear)")
    print("  [0] Regresar")
    choice = input(f"\n{Colors.YELLOW}Selecciona una opción: {Colors.RESET}").strip()

    if choice == "1":
        msg = input(f"{Colors.YELLOW}Descripción del stash (opcional): {Colors.RESET}").strip()
        args = ["stash", "push", "-u"]
        if msg:
            args.extend(["-m", msg])
        run_git(args, capture=False)
        print_success("Cambios resguardados.")
    elif choice == "2":
        run_git(["stash", "pop"], capture=False)
    elif choice == "3":
        out, _, _ = run_git(["stash", "list"])
        if out:
            print(f"\n{out}")
        else:
            print_info("No hay stashes almacenados.")
    elif choice == "4":
        confirm = input(f"{Colors.RED}¿Seguro de vaciar todo el stash? (s/n): {Colors.RESET}").lower()
        if confirm in ['s', 'si', 'y', 'yes']:
            run_git(["stash", "clear"], capture=False)
            print_success("Stash vaciado.")

def cmd_log(limit=10):
    """Muestra el historial de commits con formato gráfico."""
    print_header(f"HISTORIAL DE COMMITS (Últimos {limit})")
    run_git(["log", f"-n{limit}", "--graph", "--pretty=format:%C(yellow)%h%Creset -%C(auto)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset"], capture=False)
    print()

def cmd_undo_last_commit():
    """Deshace el último commit manteniendo los cambios en tus archivos."""
    print_header("DESHACER ÚLTIMO COMMIT")
    print_warning("Esta acción deshará el último commit local manteniendo todos tus archivos modificados intactos (soft reset).")
    confirm = input(f"{Colors.YELLOW}¿Deseas continuar? (s/n): {Colors.RESET}").lower()
    if confirm in ['s', 'si', 'y', 'yes']:
        out, err, code = run_git(["reset", "--soft", "HEAD~1"])
        if code == 0:
            print_success("Último commit deshecho. Tus cambios están intactos en tu área de trabajo.")
        else:
            print_error(f"Error al deshacer commit:\n{err}")

def cmd_discard_all_changes():
    """Descarta todos los cambios locales sin commitear."""
    print_header("DESCARTAR TODOS LOS CAMBIOS NO GUARDADOS")
    print_error("¡CUIDADO! Esta acción eliminará permanentemente todas las modificaciones y archivos nuevos no guardados.")
    confirm = input(f"{Colors.RED}¿Estás COMPLETAMENTE seguro de descartar todo? (escribe 'SI'): {Colors.RESET}").strip()
    if confirm == "SI":
        run_git(["restore", "."])
        run_git(["clean", "-fd"])
        print_success("Directorio de trabajo restablecido a la versión limpia.")
    else:
        print_info("Operación cancelada.")

# ==================== MENÚ PRINCIPAL INTERACTIVO ====================

def main_interactive_menu():
    while True:
        if not is_git_repo():
            print_header("REPOSITORIO NO INICIALIZADO")
            print_warning("Este directorio no es un repositorio Git.")
            init = input(f"{Colors.YELLOW}¿Deseas inicializarlo ahora (git init)? (s/n): {Colors.RESET}").lower()
            if init in ['s', 'si', 'y', 'yes']:
                run_git(["init"])
                print_success("Repositorio Git inicializado.")
            else:
                break

        curr_branch = get_current_branch()
        remote = get_remote_name()
        ahead = get_ahead_behind()
        changes = len(get_changes_summary())
        status_txt = f"{changes} archivo(s) con cambios" if changes > 0 else "Limpio"

        print(f"\n{Colors.BOLD}{Colors.CYAN}============================================================{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}             🛠️   GIT MANAGER AUTOMATIZADO 🚀{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}============================================================{Colors.RESET}")
        print(f"  {Colors.BOLD}Rama actual:{Colors.RESET} {Colors.GREEN}[ {curr_branch} ]{Colors.RESET}  |  {Colors.BOLD}Remoto:{Colors.RESET} {Colors.CYAN}[ {remote} ]{Colors.RESET}")
        print(f"  {Colors.BOLD}Estado:{Colors.RESET}      {Colors.YELLOW}{status_txt}{Colors.RESET} {Colors.CYAN}{ahead}{Colors.RESET}")
        print(f"{Colors.CYAN}------------------------------------------------------------{Colors.RESET}")
        print(f"  {Colors.BOLD}[1]  ⚡ Auto-Sync Completo{Colors.RESET} (Pull inteligente + Add + Commit + Push)")
        print(f"  {Colors.BOLD}[2]  🚀 Guardar y Subir Rápido{Colors.RESET} (Add + Commit + Push)")
        print(f"  {Colors.BOLD}[3]  📥 Descargar cambios{Colors.RESET} (Smart Pull con auto-stash)")
        print(f"  {Colors.BOLD}[4]  🌿 Crear nueva rama y cambiarte a ella{Colors.RESET}")
        print(f"  {Colors.BOLD}[5]  🔀 Cambiar de rama (Menú interactivo){Colors.RESET}")
        print(f"  {Colors.BOLD}[6]  🤝 Fusionar rama (Merge a la rama actual){Colors.RESET}")
        print(f"  {Colors.BOLD}[7]  🗑️  Eliminar rama (Local / Remota){Colors.RESET}")
        print(f"  {Colors.BOLD}[8]  📊 Ver estado detallado y cambios{Colors.RESET}")
        print(f"  {Colors.BOLD}[9]  📜 Ver historial de commits (Log gráfico){Colors.RESET}")
        print(f"  {Colors.BOLD}[10] 📦 Stash (Guardar/Recuperar cambios temporales){Colors.RESET}")
        print(f"  {Colors.BOLD}[11] ⏪ Deshacer último commit (manteniendo archivos){Colors.RESET}")
        print(f"  {Colors.BOLD}[12] 🧹 Descartar cambios sin guardar (Limpieza total){Colors.RESET}")
        print(f"  {Colors.BOLD}[0]  🚪 Salir{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}============================================================{Colors.RESET}")

        opc = input(f"{Colors.YELLOW}Selecciona una opción [0-12]: {Colors.RESET}").strip()

        if opc == "1":
            cmd_full_auto_sync()
        elif opc == "2":
            cmd_quick_push()
        elif opc == "3":
            cmd_smart_pull()
        elif opc == "4":
            cmd_create_branch()
        elif opc == "5":
            cmd_switch_branch()
        elif opc == "6":
            cmd_merge_branch()
        elif opc == "7":
            cmd_delete_branch()
        elif opc == "8":
            cmd_status()
        elif opc == "9":
            cmd_log()
        elif opc == "10":
            cmd_stash_menu()
        elif opc == "11":
            cmd_undo_last_commit()
        elif opc == "12":
            cmd_discard_all_changes()
        elif opc == "0":
            print(f"\n{Colors.GREEN}¡Hasta pronto!{Colors.RESET}\n")
            break
        else:
            print_error("Opción inválida. Elige un número del 0 al 12.")

        input(f"\n{Colors.GRAY}Presiona Enter para continuar...{Colors.RESET}")

# ==================== PARSER DE LÍNEA DE COMANDOS ====================

def main():
    parser = argparse.ArgumentParser(
        description="Gestor y Automatizador de Flujo de Trabajo en Git",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso directo:
  python git_manager.py sync                      # Pull + Add + Commit + Push automatizado
  python git_manager.py push -m "fix login bug"   # Add + Commit + Push en 1 paso
  python git_manager.py pull                      # Pull inteligente con auto-stash
  python git_manager.py branch nueva-funcionalidad # Crea y cambia a la nueva rama
  python git_manager.py switch dev                # Cambia a la rama dev
  python git_manager.py status                    # Muestra el estado del repo
  python git_manager.py                           # Abre el Menú Interactivo Completo
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")

    # Comando sync
    p_sync = subparsers.add_parser("sync", help="Sincronización completa: Pull + Add + Commit + Push")
    p_sync.add_argument("-m", "--message", help="Mensaje del commit (opcional)")

    # Comando push
    p_push = subparsers.add_parser("push", help="Guarda y sube cambios (Add + Commit + Push)")
    p_push.add_argument("-m", "--message", help="Mensaje del commit")

    # Comando pull
    subparsers.add_parser("pull", help="Descarga cambios con stash automático de cambios locales")

    # Comando status
    subparsers.add_parser("status", help="Muestra el estado detallado del repositorio")

    # Comando branch
    p_branch = subparsers.add_parser("branch", help="Crea una nueva rama")
    p_branch.add_argument("name", help="Nombre de la nueva rama")
    p_branch.add_argument("--no-checkout", action="store_true", help="No cambiarse a la rama tras crearla")
    p_branch.add_argument("--push", action="store_true", help="Publicar la rama al remoto de inmediato")

    # Comando switch
    p_switch = subparsers.add_parser("switch", help="Cambia a una rama existente")
    p_switch.add_argument("name", nargs="?", help="Nombre de la rama (si se omite, muestra lista)")

    # Comando merge
    p_merge = subparsers.add_parser("merge", help="Fusiona una rama en la actual")
    p_merge.add_argument("name", nargs="?", help="Nombre de la rama a fusionar")

    # Comando log
    p_log = subparsers.add_parser("log", help="Muestra el historial de commits")
    p_log.add_argument("-n", "--limit", type=int, default=10, help="Número de commits a mostrar (defecto: 10)")

    # Comando undo
    subparsers.add_parser("undo", help="Deshace el último commit manteniendo tus archivos intactos")

    args = parser.parse_args()

    if not args.command:
        # Modo interactivo si no se pasan argumentos
        main_interactive_menu()
    else:
        if args.command == "sync":
            cmd_full_auto_sync(message=args.message)
        elif args.command == "push":
            cmd_quick_push(message=args.message)
        elif args.command == "pull":
            cmd_smart_pull()
        elif args.command == "status":
            cmd_status()
        elif args.command == "branch":
            cmd_create_branch(branch_name=args.name, checkout=not args.no_checkout, push_upstream=args.push)
        elif args.command == "switch":
            cmd_switch_branch(branch_name=args.name)
        elif args.command == "merge":
            cmd_merge_branch(branch_name=args.name)
        elif args.command == "log":
            cmd_log(limit=args.limit)
        elif args.command == "undo":
            cmd_undo_last_commit()

if __name__ == "__main__":
    main()
