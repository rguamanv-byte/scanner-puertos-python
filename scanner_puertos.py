"""
===============================================================
 ESCÁNER DE PUERTOS DE RED
 Universidad Estatal de Milagro (UNEMI) Grupo #10
 Lenguaje: Python 3 | Biblioteca principal: socket
===============================================================

Descripción:
    Programa de consola que verifica qué puertos TCP se
    encuentran abiertos en un equipo dentro de un rango
    definido por el usuario.

Uso interactivo:
    python scanner_puertos.py 

Uso directo (opcional):
    python scanner_puertos.py 127.0.0.1 1 100

AVISO: Este programa es de uso académico. Debe ejecutarse
únicamente sobre equipos propios, máquinas virtuales o redes
en las que se cuente con autorización expresa.
"""

===============================================================
 INTEGRANTES:
 Genaro Arias
 Rolando Guaman
 Ximena Cardenas
 Milly Castro
 Kevin Bazurto
 Dario Añasca
===============================================================

import socket
import sys
import ipaddress
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# --------------------------------------------------------------
# CONFIGURACIÓN GENERAL
# --------------------------------------------------------------
TIEMPO_ESPERA = 0.5   # Segundos de espera por cada puerto
MAX_HILOS = 100       # Conexiones simultáneas (acelera el escaneo)
ANCHO = 52            # Ancho de las líneas decorativas

# --------------------------------------------------------------
# FUNCIONES DE PRESENTACIÓN
# --------------------------------------------------------------
def mostrar_titulo():
    """Imprime el encabezado del programa."""
    print("=" * ANCHO)
    print("ESCÁNER DE PUERTOS".center(ANCHO))
    print("=" * ANCHO)

def mostrar_aviso():
    """Muestra el aviso de uso responsable y pide confirmación."""
    print("Uso académico. Escanee solamente equipos propios,")
    print("máquinas virtuales o redes autorizadas.")
    respuesta = input("¿Cuenta con autorización para escanear? (s/n): ").strip().lower()
    if respuesta not in ("s", "si", "sí"):
        print("\nOperación cancelada por el usuario.")
        sys.exit(0)
    print("-" * ANCHO)

def mostrar_progreso(analizados, total):
    """Muestra el avance del escaneo actualizando una sola línea."""
    # Se refresca cada 1% para no saturar la consola
    paso = max(1, total // 100)
    if analizados % paso != 0 and analizados != total:
        return
    porcentaje = (analizados / total) * 100
    print(f"\rEscaneando... {analizados}/{total} ({porcentaje:5.1f}%)",
          end="", flush=True)

# --------------------------------------------------------------
# FUNCIONES DE VALIDACIÓN Y ENTRADA DE DATOS
# --------------------------------------------------------------
def resolver_objetivo(entrada):
    """
    Devuelve la dirección IP del objetivo.
    Acepta una IP (192.168.1.10) o un nombre de host (localhost).
    Retorna None si el dato no es válido.
    """
    try:
        ipaddress.ip_address(entrada)   # ¿Es una IP válida?
        return entrada
    except ValueError:
        pass

    try:
        return socket.gethostbyname(entrada)   # ¿Es un nombre resoluble?
    except socket.gaierror:
        return None


def pedir_ip():
    """Solicita al usuario la dirección IP y la valida."""
    while True:
        entrada = input("IP: ").strip()
        if not entrada:
            print("  [!] Debe ingresar una dirección IP o un nombre de host.")
            continue

        ip = resolver_objetivo(entrada)
        if ip is None:
            print(f"  [!] No se pudo resolver '{entrada}'. Verifique el dato.")
            continue

        if ip != entrada:
            print(f"  -> '{entrada}' corresponde a la IP {ip}")
        return ip


def pedir_puerto(mensaje, minimo=1):
    """
    Solicita un número de puerto válido (entre 1 y 65535).
    El parámetro 'minimo' se usa para validar el puerto final.
    """
    while True:
        dato = input(mensaje).strip()
        if not dato.isdigit():
            print("  [!] Ingrese únicamente números enteros.")
            continue

        puerto = int(dato)
        if puerto < 1 or puerto > 65535:
            print("  [!] El puerto debe estar entre 1 y 65535.")
            continue
        if puerto < minimo:
            print(f"  [!] El puerto final no puede ser menor que {minimo}.")
            continue
        return puerto


# --------------------------------------------------------------
# FUNCIONES DEL ESCANEO
# --------------------------------------------------------------
def nombre_servicio(puerto):
    """Devuelve el servicio asociado al puerto (si el sistema lo conoce)."""
    try:
        return socket.getservbyport(puerto, "tcp")
    except OSError:
        return "desconocido"


def escanear_puerto(ip, puerto):
    """
    Intenta conectarse a un puerto TCP.
    Retorna el número de puerto si está ABIERTO, o None si está cerrado.

    connect_ex() devuelve 0 cuando la conexión es exitosa.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conexion:
            conexion.settimeout(TIEMPO_ESPERA)
            if conexion.connect_ex((ip, puerto)) == 0:
                return puerto
    except socket.error:
        pass
    return None


def escanear_rango(ip, puerto_inicial, puerto_final):
    """
    Recorre el rango de puertos y devuelve la lista de puertos abiertos.
    Se usan varios hilos para reducir el tiempo de espera total.
    """
    puertos = range(puerto_inicial, puerto_final + 1)
    total = len(puertos)
    abiertos = []
    analizados = 0

    with ThreadPoolExecutor(max_workers=min(MAX_HILOS, total)) as ejecutor:
        for resultado in ejecutor.map(lambda p: escanear_puerto(ip, p), puertos):
            analizados += 1
            if resultado is not None:
                abiertos.append(resultado)
            mostrar_progreso(analizados, total)

    print()   # Salto de línea al terminar la barra de progreso
    return sorted(abiertos)


# --------------------------------------------------------------
# FUNCIONES DE RESULTADOS
# --------------------------------------------------------------
def mostrar_resultados(abiertos):
    """Lista los puertos abiertos encontrados."""
    print("-" * ANCHO)
    if not abiertos:
        print("No se encontraron puertos abiertos en el rango indicado.")
        return

    for puerto in abiertos:
        print(f"Puerto {puerto} - ABIERTO   ({nombre_servicio(puerto)})")


def mostrar_resumen(ip, inicio, fin, abiertos, duracion):
    """Muestra el resumen final del escaneo."""
    total = fin - inicio + 1
    print("-" * ANCHO)
    print("RESUMEN DEL ESCANEO")
    print(f"Equipo analizado : {ip}")
    print(f"Rango de puertos : {inicio} - {fin}")
    print(f"Puertos analizados: {total}")
    print(f"Puertos abiertos  : {len(abiertos)}")
    print(f"Puertos cerrados  : {total - len(abiertos)}")
    print(f"Tiempo empleado   : {duracion:.2f} segundos")
    print("=" * ANCHO)

# --------------------------------------------------------------
# PROGRAMA PRINCIPAL
# --------------------------------------------------------------
def main():
    mostrar_titulo()

    # Modo directo: python scanner_puertos.py IP INICIO FIN
    if len(sys.argv) == 4:
        ip = resolver_objetivo(sys.argv[1])
        if ip is None:
            print("Dirección IP o host no válido.")
            sys.exit(1)
        puerto_inicial = int(sys.argv[2])
        puerto_final = int(sys.argv[3])
        print(f"IP: {ip}")
        print(f"Desde: {puerto_inicial}")
        print(f"Hasta: {puerto_final}")
    else:
        mostrar_aviso()
        ip = pedir_ip()
        puerto_inicial = pedir_puerto("Desde: ")
        puerto_final = pedir_puerto("Hasta: ", minimo=puerto_inicial)

    print("-" * ANCHO)
    inicio_tiempo = datetime.now()
    abiertos = escanear_rango(ip, puerto_inicial, puerto_final)
    duracion = (datetime.now() - inicio_tiempo).total_seconds()

    mostrar_resultados(abiertos)
    mostrar_resumen(ip, puerto_inicial, puerto_final, abiertos, duracion)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nEscaneo interrumpido por el usuario.")
        sys.exit(0)
