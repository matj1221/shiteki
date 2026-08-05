import time
import random
import ctypes
import win32gui
import win32con
from pynput.mouse import Button, Controller as MouseController

mouse = MouseController()

# Estructuras nativas de Win32 para enviar Scan Codes directos al motor de CS2
SendInput = ctypes.windll.user32.SendInput

# Mapas de Scan Codes de teclado hardware
SCAN_CODES = {
    'w': 0x11,
    'a': 0x1E,
    's': 0x1F,
    'd': 0x20,
    'space': 0x39
}

PUL_INPUT = ctypes.POINTER(ctypes.c_ulong)

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL_INPUT)]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL_INPUT)]

class INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT),
                ("mi", MOUSEINPUT),
                ("hi", HARDWAREINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", INPUT_UNION)]

def presionar_tecla_hardware(tecla):
    code = SCAN_CODES.get(tecla)
    if not code: return
    extra = ctypes.c_ulong(0)
    ii_ = INPUT_UNION()
    ii_.ki = KEYBDINPUT(0, code, 0x0008, 0, ctypes.pointer(extra)) # 0x0008 = KEYEVENTF_SCANCODE
    x = INPUT(1, ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def soltar_tecla_hardware(tecla):
    code = SCAN_CODES.get(tecla)
    if not code: return
    extra = ctypes.c_ulong(0)
    ii_ = INPUT_UNION()
    ii_.ki = KEYBDINPUT(0, code, 0x0008 | 0x0002, 0, ctypes.pointer(extra)) # 0x0002 = KEYEVENTF_KEYUP
    x = INPUT(1, ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def obtener_todas_las_ventanas(subcadena_titulo):
    ventanas_encontradas = []
    def enum_windows_callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            texto_ventana = win32gui.GetWindowText(hwnd)
            if subcadena_titulo.lower() in texto_ventana.lower():
                ventanas_encontradas.append(hwnd)
        return True
    win32gui.EnumWindows(enum_windows_callback, None)
    ventanas_encontradas.sort()
    return ventanas_encontradas

def forzar_foco_ventana(hwnd):
    try:
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            
        win32gui.SetForegroundWindow(hwnd)
        
        for _ in range(5):
            if win32gui.GetForegroundWindow() == hwnd:
                return True
            time.sleep(0.05)
            win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass
    return win32gui.GetForegroundWindow() == hwnd

def enviar_movimiento(hwnd, indice):
    teclas_a_presionar = []
    try:
        if not forzar_foco_ventana(hwnd):
            print(f"[Aviso] No se obtuvo foco para Instancia {indice + 1} (HWND: {hwnd}). Omitiendo...")
            return

        time.sleep(0.3)

        teclas_posibles = ['w', 'a', 's', 'd']
        teclas_a_presionar = random.sample(teclas_posibles, k=random.choice([1, 2]))
        
        # Aumentamos la duración de la caminata (de 1.5s a 3.5s)
        duracion_caminata = random.uniform(1.5, 3.5)
        debe_saltar = random.choice([True, False])
        debe_disparar = random.choice([True, False])

        # 1. Movimiento de vista
        dx = random.randint(-100, 100)
        dy = random.randint(-40, 40)
        mouse.move(dx, dy)
        time.sleep(0.05)

        # 2. Caminar / Saltar usando Scan Codes Directos
        try:
            for t in teclas_a_presionar:
                presionar_tecla_hardware(t)

            if debe_saltar:
                mitad = duracion_caminata / 2.0
                time.sleep(mitad)
                presionar_tecla_hardware('space')
                time.sleep(0.1)
                soltar_tecla_hardware('space')
                time.sleep(max(0, mitad - 0.1))
            else:
                time.sleep(duracion_caminata)
        finally:
            for t in teclas_a_presionar:
                soltar_tecla_hardware(t)

        # 3. Disparo
        if debe_disparar:
            time.sleep(0.1)
            mouse.press(Button.left)
            time.sleep(random.uniform(0.08, 0.18))
            mouse.release(Button.left)

        str_teclas = "+".join(teclas_a_presionar).upper()
        print(f"[Instancia {indice + 1} | HWND: {hwnd}] Teclas HW: {str_teclas} ({duracion_caminata:.2f}s) | Salto: {debe_saltar} | Disparo: {debe_disparar}")

    except Exception as e:
        print(f"[Error] Instancia {indice + 1} (HWND: {hwnd}): {e}")

def espera_interrumpible(segundos):
    enteros = int(segundos)
    fraccion = segundos - enteros
    for _ in range(enteros):
        time.sleep(1)
    if fraccion > 0:
        time.sleep(fraccion)

# --- BUCLE PRINCIPAL ---
if __name__ == "__main__":
    print("Iniciando script AFK (Modo Hardware ScanCodes) en 5 segundos...")
    time.sleep(5)
    
    while True:
        instancias = obtener_todas_las_ventanas("Counter-Strike 2")
        print(f"\n==========================================")
        print(f"Escaneando... ¡Se encontraron {len(instancias)} instancias activas!")
        print(f"==========================================")
        
        if len(instancias) == 0:
            print("No se encontraron ventanas. Reintentando en 10s...")
            espera_interrumpible(10)
            continue

        for i, hwnd in enumerate(instancias):
            enviar_movimiento(hwnd, i)
            time.sleep(1.2)
            
        # Reducimos el tiempo entre rondas a 30-50 segundos para renovar el temporizador AFK del servidor
        espera = random.uniform(30, 50)
        print(f"\n--- Ciclo finalizado. Esperando {espera:.1f}s para la siguiente ronda ---")
        espera_interrumpible(espera)