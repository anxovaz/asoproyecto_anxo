import docker
import os
import time
import subprocess
import sys

import docker.errors

client = docker.from_env()

current_directory = os.path.dirname(os.path.abspath(__file__))


def apache_local():
    try:
        print("Reinstalando apache2...")
        subprocess.run(["sudo", "apt", "update", "-y"], check=True, stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w'))
        subprocess.run(["sudo", "apt", "autoremove", "apache2", "-y"], check=True, stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w'))
        subprocess.run(["sudo", "apt", "install", "apache2", "-y"], check=True, stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w'))
        ruta_conf_apache_local = "/config/apache_local/conf"
        conf_apache_local = os.path.join(current_directory, ruta_conf_apache_local.lstrip('/'))
        ruta_html_apache_local = "/config/apache_local/html"
        html_apache_local = os.path.join(current_directory, ruta_html_apache_local.lstrip('/'))
        ruta_script = "python.py"
        script_apache_local = os.path.join(current_directory, ruta_script)
        print("Copiando archivos de configuración")
        subprocess.run(["sudo", "rm", "-rf", "/var/www/html/*"], check=True, stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w'))
        subprocess.run(["sudo", "rm", "-rf", "/etc/apache2/*"], check=True, stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w'))
        subprocess.run(["sudo", "cp", "-r", conf_apache_local, "/etc/apache2/"], check=True, stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w'))
        subprocess.run(["sudo", "cp", "-r", html_apache_local, "/var/www/"], check=True, stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w'))
        subprocess.run(["sudo", "cp", script_apache_local, "/mnt/"], check=True, stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w'))
        subprocess.run(["sudo", "chmod", "777", "/mnt/python.py"], check=True, stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w'))
        subprocess.run(["sudo", "systemctl", "start", "apache2"], check=True, stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w'))
        subprocess.run(["sudo", "systemctl", "enable", "apache2"], check=True, stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w'))
        print("Accede a localhost:8080 para administrar los contenedores")
        
    except subprocess.CalledProcessError as e:
        print(f"Error al instalar: {e}")
        
def parar_systemresolved():
    try:
        subprocess.run(["sudo", "systemctl", "stop", "systemd-resolved"], check=True)
        print("Servicio systemd-resolved detenido exitosamente.")
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar el comando: {e}")
    except FileNotFoundError:
        print("Comando no encontrado. Asegúrate de tener 'systemctl' instalado.")

def reanudar_systemresolved():
    try:
        subprocess.run(["sudo", "systemctl", "restart", "systemd-resolved"], check=True)
        print("Servicio systemd-resolved reiniciado exitosamente.")
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar el comando: {e}")
    except FileNotFoundError:
        print("Comando no encontrado. Asegúrate de tener 'systemctl' instalado.")

def parar_contenedor(parar_contenedor):
    client = docker.from_env()
    containers = client.containers.list(all=True)
    container_exists = False
    container_to_remove = None

    for container in containers:
        if container.name == parar_contenedor:
            container_exists = True
            container_to_stop = container
            break
    if container_exists:
        print(f"Contenedor '{parar_contenedor}' encontrado, deteniéndolo.")
        container_to_stop.stop()  # Detener el contenedor si está en ejecución
        print(f"Contenedor '{parar_contenedor}' detenido.")
    else:
        print(f"El contenedor '{parar_contenedor}' no existe.")

def eliminar_contenedor(nombre_contenedor):
    try:
        # Crear el cliente Docker
        client = docker.from_env()

        # Obtener el contenedor por nombre
        container = client.containers.get(nombre_contenedor)

        # Detener y eliminar el contenedor
        container.stop()
        container.remove()

        print(f"Contenedor '{nombre_contenedor}' detenido y eliminado exitosamente.")
    
    except docker.errors.NotFound:
        print(f"Error: El contenedor '{nombre_contenedor}' no se encuentra.")
    except docker.errors.APIError as e:
        print(f"Error al interactuar con la API de Docker: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")

def continuar_contenedor(continuar_contenedor):
    client = docker.from_env()
    containers = client.containers.list(all=True)
    container_exists = False
    container_to_continue = None

    for container in containers:
        if container.name == continuar_contenedor:
            container_exists = True
            container_to_continue = container
            break
    if container_exists:
        print(f"Contenedor '{continuar_contenedor}' encontrado, continuándolo.")
        container_to_continue.start()  # Detener el contenedor si está en ejecución
        print(f"Contenedor '{continuar_contenedor}' reanuado.")
    else:
        print(f"El contenedor '{continuar_contenedor}' no existe.")


def crear_red():
    try:
        # Crear el cliente Docker
        client = docker.from_env()

        # Comprobar si la red ya existe
        redes_existentes = client.networks.list(names=["red"])
        if redes_existentes:
            print("La red 'red' ya existe.")
        else:
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



def eliminar_contenedor(nombre_contenedor):
    try:
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
    
    except Exception as e:
        print(f"Error inesperado: {e}")


def apacheserver():
    nombre_contenedor_apache = "apache"
    eliminar_contenedor(nombre_contenedor_apache)

    # Ruta adicional
    htdocs = "/config/apache/htdocs"
    html = os.path.join(current_directory, htdocs.lstrip('/'))  # Unir las rutas



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
    dirconf = "/config/bind9/conf"
    conf_bind9_ruta = os.path.join(current_directory, dirconf.lstrip('/'))  # Unir las rutas
    dirzonas = "/config/bind9/zonas"
    zonas_bind9_ruta = os.path.join(current_directory, dirzonas.lstrip('/'))


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

def mysql():
    try:
        eliminar_contenedor("mysql")
        dir_data="/config/mysql/data"
        data=os.path.join(current_directory, dir_data.lstrip('/'))
        dir_cnf="/config/mysql/cnf"
        cnf=os.path.join(current_directory,dir_cnf.lstrip('/'))
        dir_script_bash="/config/mysql/root_acceso.sh"
        script=os.path.join(current_directory,dir_script_bash.lstrip('/'))

        nombrecontenedor_mysql="mysql"
        client=docker.from_env()
        container = client.containers.run(
        "mysql:latest",  # Usar la imagen oficial de MySQL
        name=nombrecontenedor_mysql,
        environment={
            "MYSQL_ROOT_PASSWORD": "123456",
            "MYSQL_ROOT_HOST": "%"
            },
        volumes={data: {"bind": "/var/lib/mysql", "mode": "rw"},
                cnf: {"bind": "/etc/mysql", "mode": "rw"},
                script: {"bind": "/mnt/root_acceso.sh", "mode": "rw"}},

        network="red",
        networking_config={
                'red': client.api.create_endpoint_config(
                    ipv4_address="192.168.250.40"
                )
            },
        ports={'3306/tcp': 3306},  # Exponer el puerto 3306
        detach=True,  # Ejecutar en segundo plano
        )
        print(f"Contenedor {nombrecontenedor_mysql} ejecutándose.")
    except docker.errors.APIError as e:
        print(f"Error al crear contenedor; {e}")

def phpmyadmin():
    try:
        eliminar_contenedor("phpmyadmin")
        client.containers.run(
        "phpmyadmin:latest",
        name="phpmyadmin",
        environment={
            "PMA_HOST": "192.168.250.40",  # IP estática del contenedor MySQL
            "PMA_PORT": 3306,
            "PMA_USER": "admin",
            "PMA_PASSWORD": "123456"
        },
        network="red",
        networking_config={
                'red': client.api.create_endpoint_config(
                    ipv4_address="192.168.250.50"
                )
            },
        ports={'80/tcp': 5000},
        detach=True,
    )
    except Exception as e:
        print(f"Error al arrancar contenedor phpmyadmin: {e}")

#Arreglar
def ldap():
    try:
        eliminar_contenedor("ldap")
        ldap_data="/config/ldap/data"
        ruta_ldap_data=os.path.join(current_directory,ldap_data.lstrip('/'))
        ldap_conf="/config/ldap/conf"
        ruta_ldap_conf=os.path.join(current_directory,ldap_conf.lstrip('/'))

        os.makedirs(ruta_ldap_data, exist_ok=True)
        os.makedirs(ruta_ldap_conf, exist_ok=True)
        subprocess.run(f"sudo chown -R 1001:1001 {ruta_ldap_data}", shell=True)
        subprocess.run(f"sudo chown -R 1001:1001 {ruta_ldap_conf}", shell=True)


        client.containers.run(
        "bitnami/openldap",
        name="ldap",
        ports={'389/tcp': 389, '636/tcp': 636},
        network="red",
        networking_config={
                'red': client.api.create_endpoint_config(
                    ipv4_address="192.168.250.60"
                )
            },
        volumes={
                ruta_ldap_conf: {'bind': '/opt/bitnami/openldap/etc', 'mode': 'rw'},
                ruta_ldap_data: {'bind': '/bitnami/openldap', 'mode': 'rw'}
            },
        
        detach=True,
        )
    
    except Exception as e:
        print(f"Error al crear el contenedor ldap: {e}")

def portainer():
    client = docker.from_env()

    nombrecontenedor_portainer = "portainer"
    eliminar_contenedor(nombrecontenedor_portainer)
    ruta_data="/config/portainer/data"
    ruta_portainer_data=os.path.join(current_directory,ruta_data.lstrip('/'))


    try:
        container = client.containers.run(
            "portainer/portainer-ce",
            name=nombrecontenedor_portainer,
            ports={"9000/tcp": 5001},
            volumes={"/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "rw"},
                    ruta_portainer_data: {"bind": "/data", "mode": "rw"}},
            restart_policy={"Name": "always"},
            network="red",
            networking_config={
                'red': client.api.create_endpoint_config(
                    ipv4_address="192.168.250.70"
                )
            },
            detach=True
        )
        print(f"Contenedor {nombrecontenedor_portainer} ejecutandose")
    except docker.errors.APIError as e:
        print(f"Error al crear el contenedor {e}")    

# Verificar si el parámetro pasado es "samba"
if len(sys.argv) > 1 and sys.argv[1] == "--launch-samba":
    crear_red()
    samba()

elif len(sys.argv) > 1 and sys.argv[1] == "--stop-samba":
    parar_contenedor("samba")

elif len(sys.argv) > 1 and sys.argv[1] == "--continue-samba":
    continuar_contenedor("samba")

elif len(sys.argv) > 1 and sys.argv[1] == "--eliminar-samba":
    eliminar_contenedor("samba")

elif len(sys.argv) > 1 and sys.argv[1] == "--launch-apache":
    crear_red()
    apacheserver()

elif len(sys.argv) > 1 and sys.argv[1] == "--stop-apache":
    parar_contenedor("apache")

elif len(sys.argv) > 1 and sys.argv[1] == "--continue-apache":
    continuar_contenedor("apache")

elif len(sys.argv) > 1 and sys.argv[1] == "--eliminar-apache":
    eliminar_contenedor("apache")

elif len(sys.argv) > 1 and sys.argv[1] == "--launch-bind9":
    crear_red()
    parar_systemresolved()
    bind9server()
   
elif len(sys.argv) > 1 and sys.argv[1] == "--stop-bind9":
    parar_contenedor("bind9")
    reanudar_systemresolved()

elif len(sys.argv) > 1 and sys.argv[1] == "--continue-bind9":
    parar_systemresolved()
    continuar_contenedor("bind9")

elif len(sys.argv) > 1 and sys.argv[1] == "--eliminar-bind9":
    eliminar_contenedor("bind9")
    reanudar_systemresolved()

elif len(sys.argv) > 1 and sys.argv[1] == "--help":
    print("--launch-samba")
    print("--stop-samba")
    print("--continue-samba")
    print("--eliminar-samba")
    print("--launch-apache")
    print("--stop-apache")
    print("--continue-apache")
    print("--eliminar-apache")
    print("--launch-bind9")
    print("--stop-bind9")
    print("--continue-bind9")
    print("--eliminar-bind9")
    print("--help")

else:
    #apache_local()
    crear_red()
    print("***********************************************************")
    apacheserver()
    parar_contenedor("apache")
    print("***********************************************************")
    parar_systemresolved()
    bind9server()
    parar_contenedor("bind9")
    reanudar_systemresolved()
    print("***********************************************************")
    samba()
    parar_contenedor("samba")
    print("***********************************************************")
    mysql()
    parar_contenedor("mysql")
    print("***********************************************************")
    phpmyadmin()
    parar_contenedor("phpmyadmin")
    print("**********************************************************")
    ldap()
    #parar_contenedor("ldap")
    print("***********************************************************")
    print("admin, admin12345678")
    portainer()
