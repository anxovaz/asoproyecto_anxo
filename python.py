import docker
import os
import time
import subprocess
import sys

client = docker.from_env()

current_directory = os.path.dirname(os.path.abspath(__file__))
print(f"El directorio actual del script es: {current_directory}")

def parar_systemresolved():
    try:
        subprocess.run(["sudo", "systemctl", "stop", "systemd-resolved"], check=True)
        print("Servicio systemd-resolved detenido exitosamente.")
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar el comando: {e}")
    except FileNotFoundError:
        print("Comando no encontrado. Asegúrate de tener 'systemctl' instalado.")

parar_systemresolved()

def crear_red():
    try:
        # Crear el cliente Docker
        client = docker.from_env()

        # Crear la red con la subred especificada
        red = client.networks.create(
            "red",        # Nombre de la red
            driver="bridge",   # Tipo de red (por ejemplo, "bridge", "host", "overlay")
            ipam=docker.types.IPAMConfig(
                pool_configs=[docker.types.IPAMPool(
                    subnet="192.168.250.0/24",  # Subred especificada
                )]
            )
        )

        print(f"Red creada exitosamente con el driver 'bridge' y subnet '192.168.250.0/24'")
    except docker.errors.APIError as e:
        print(f"Error al crear la red: {e}")

# Llamar a la función para crear la red
crear_red()


def eliminar_contenedor(nombre_contenedor):
    try:
        # Inicializar el cliente Docker
        client = docker.from_env()

        # Obtener todos los contenedores (incluyendo detenidos)
        containers = client.containers.list(all=True)

        # Inicializar la variable que indicará si el contenedor existe
        container_exists = False
        container_to_remove = None

        # Iterar sobre los contenedores para buscar el que tenga el nombre especificado
        for container in containers:
            if container.name == nombre_contenedor:
                container_exists = True
                container_to_remove = container
                break  # Salimos del bucle si encontramos el contenedor

        # Si el contenedor existe, detenerlo y eliminarlo
        if container_exists:
            print(f"Contenedor '{nombre_contenedor}' encontrado. Deteniéndolo y eliminándolo.")
            container_to_remove.stop()  # Detener el contenedor si está en ejecución
            container_to_remove.remove()  # Eliminar el contenedor
            print(f"Contenedor '{nombre_contenedor}' detenido y eliminado.")
        else:
            print(f"El contenedor '{nombre_contenedor}' no existe.")
    
    except NotFound:
        print(f"Error: El contenedor '{nombre_contenedor}' no se encuentra.")
    except DockerException as e:
        print(f"Error en la ejecución de la función eliminar_contenedor: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")


def apacheserver():
    # Crear el cliente Docker
    client = docker.from_env()

    nombre_contenedor_apache = "apache"
    eliminar_contenedor(nombre_contenedor_apache)

    # Ruta adicional
    htdocs = "/config/apache/htdocs"
    html = os.path.join(current_directory, htdocs.lstrip('/'))  # Unir las rutas

    print(f"HTML: {html}")

    # Verificar si el archivo existe

    try:
        container = client.containers.run(
            "php:7.4-apache",
            name=nombre_contenedor_apache,
            network="red",
            detach=True,
            volumes={html: {"bind": "/var/www/html", "mode": "rw"}},
            ports={'80/tcp': 80},
            # Configuración especial para IP fija
            networking_config={
                'red': client.api.create_endpoint_config(
                    ipv4_address="192.168.250.10"
                )
            }
        )
        print(f"Contenedor {nombre_contenedor_apache} ejecutándose. Accede a http://localhost o  ejemploanxo.com en tu navegador.")
    except docker.errors.APIError as e:
        print(f"Error al crear el contenedor: {e}")


def bind9server():
    # Crear el cliente Docker
    client = docker.from_env()

    # Archivos
    dirconf = "/config/bind9/conf"
    conf_bind9_ruta = os.path.join(current_directory, dirconf.lstrip('/'))  # Unir las rutas
    print(f"El directorio de conf: {conf_bind9_ruta}")
    dirzonas = "/config/bind9/zonas"
    zonas_bind9_ruta = os.path.join(current_directory, dirzonas.lstrip('/'))
    print(f"El directorio de zonas: {zonas_bind9_ruta}")

    #comprobar si existe
    nombrecontenedor_bind9 = "bind9"
    eliminar_contenedor(nombrecontenedor_bind9)
    try:
        container = client.containers.run(
            "ubuntu/bind9",
            name=nombrecontenedor_bind9,
            network="red",
            detach=True,
            volumes={conf_bind9_ruta: {"bind": "/etc/bind", "mode": "ro"},
                    zonas_bind9_ruta: {"bind": "/var/lib/bind", "mode": "rw"}},
            ports={'53/tcp': 53, "53/udp": 53},
            networking_config={
                'red': client.api.create_endpoint_config(
                    ipv4_address="192.168.250.20"
                )
            }
        )
        print(f"Contenedor {nombrecontenedor_bind9} ejecutándose.")
    except docker.errors.APIError as e:
        print(f"Error al crear el contenedor: {e}")


def samba():
    client = docker.from_env()
    compartido = "/config/samba/compartido"
    dircompartido = os.path.join(current_directory, compartido.lstrip('/'))
    confsmb = "/config/samba/config"
    dirconfigsamba = os.path.join(current_directory, confsmb.lstrip('/'))

    nombrecontenedor_samba = "samba"
    eliminar_contenedor(nombrecontenedor_samba)

    try:
        container = client.containers.run(
            "dperson/samba",
            name=nombrecontenedor_samba,
            network="red",
            detach=True,
            volumes={dirconfigsamba: {"bind": "/etc/samba", "mode": "rw"},
                    dircompartido: {"bind": "/mnt/compartido", "mode": "rw"}},
            ports={'139/tcp': 139, '445/tcp': 445},
            networking_config={
                'red': client.api.create_endpoint_config(
                    ipv4_address="192.168.250.30"
                )
            }
        )
        print(f"Contenedor {nombrecontenedor_samba} ejecutándose.")
    except docker.errors.APIError as e:
        print(f"Error al crear el contenedor: {e}")


# Verificar si el parámetro pasado es "samba"
if len(sys.argv) > 1 and sys.argv[1] == "samba":
    samba()
    apacheserver()
    bind9server()
else:
    apacheserver()
    bind9server()
