import os
import subprocess
import sys
import time
try:
    import docker
    import docker.errors

except Exception as e:
    try:
        if os.geteuid() == 0: #si se ejecuta como root
            print("La librería docker no está instalada")
            print("Instalando la librería docker")
            subprocess.run(['sudo', 'apt-get', 'update'], check=True) #apt update
            #Instalar la librería docker
            subprocess.run(["sudo", "apt", "install", "python3-docker"], check=True)
        else: #no hay permisos de root
            print("Es necesario permisos de superusuario")
            exit(0)

    except Exception as e:
        print(f"Error al instalar librería docker: {e}")
        exit(1)

if os.geteuid() == 0: #si se ejecuta como root
    print("Script ejecutado como  root.")
    print("***********************************************************")
    try:
        #comando 'docker --version' para verificar si Docker está instalado
        resultado = subprocess.run(['docker', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        print(f"Docker está instalado: {resultado.stdout.decode().strip()}")
    except Exception:
        try:
            print("Docker no está instalado.")
            print("Instalando docker en 5 segundos, pulsa Ctrl+C para cancelar")
            time.sleep(5) #esperar a 5
            # Actualiza el sistema
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)

            # Instala ca-certificates y curl
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'ca-certificates', 'curl'], check=True)

            # Crea el directorio para la llave GPG
            subprocess.run(['sudo', 'install', '-m', '0755', '-d', '/etc/apt/keyrings'], check=True)

            # Descarga y agrega la clave GPG de Docker
            subprocess.run(['sudo', 'curl', '-fsSL', 'https://download.docker.com/linux/ubuntu/gpg', '-o', '/etc/apt/keyrings/docker.asc'], check=True)

            # Cambia los permisos de la clave GPG
            subprocess.run(['sudo', 'chmod', 'a+r', '/etc/apt/keyrings/docker.asc'], check=True)

            # Añadir el repositorio de Docker
            command = (
            'echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] '
            'https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo \"${UBUNTU_CODENAME:-$VERSION_CODENAME}\") stable" '
            '| sudo tee /etc/apt/sources.list.d/docker.list > /dev/null'
            )
            subprocess.run(command, check=True, shell=True)

            # Vuelve a actualizar la lista de paquetes
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)

            #Instalación docker
            subprocess.run(["sudo", "apt-get", "install", "docker-ce", "docker-ce-cli", "containerd.io", "docker-buildx-plugin", "docker-compose-plugin"], check=True)

            #Instalar la librería docker
            subprocess.run(["sudo", "apt", "install", "python3-docker"], check=True)

            # Después de instalar Docker
            subprocess.run(["sudo", "usermod", "-aG", "docker", os.getenv('USER')])
            print("Reinicia sesión para aplicar permisos Docker")

        except Exception as e2:
            print(f"Error al instalar docker python-pip: {e2}")
            exit(1)

else: #si no se ejecuta como root
    print("Por favor ejecute el script con permisos de superusuario")
    exit(0)  # Salir si no se ejecuta con sudo

print("En 5 segundos se ejecutará el script, pulsa Ctrl+C para cancelar")
time.sleep(5) #esperar a 5

#Inicializar cliente docker
client = docker.from_env()

#Variable que usaré más adelante para definir rutas relativas y que los contenedores no tengan problemas con los volúmenes aunque el usuario final vaya alternando la ubicación del script y carpetas
current_directory = os.path.dirname(os.path.abspath(__file__))

#Para que el contenedor con bind9 funcione correctamente en el puerto 53 es necesario tener el puerto 53 del host libre
#Puerto 53 ocupado por systemd-resolved, el de resolución de nombres de dominio
#Si este servicio se para el equipo host no podrá resolver nombres de dominio.
#Si el contenedor con bind9 no está en ejecución no podrá resolver nombres de dominio
#Si está en ejecución el equipo host usará ese contenedor para resolver nombres de dominio
def parar_systemdresolved():
    try:
        subprocess.run(["sudo", "systemctl", "stop", "systemd-resolved"], check=True)
        print("Servicio systemd-resolved detenido exitosamente.")
    except subprocess.CalledProcessError as e: #Error
        print(f"Error al ejecutar el comando: {e}")
    except FileNotFoundError: #en el caso de (no tener/tener dañado) systemctl
        print("Comando no encontrado. Asegúrate de tener 'systemctl' instalado.")

#Cuando el contenedor se para (ya sea manualmente o desde portainer) el equipo host se queda con el servicio de resolución de nombres detenido.
#Para ello reanudo el servicio de nombres cuando el contenedor se para/elimina/falla.
def reanudar_systemdresolved():
    try:
        subprocess.run(["sudo", "systemctl", "restart", "systemd-resolved"], check=True)
        print("Servicio systemd-resolved reiniciado exitosamente.")
    except subprocess.CalledProcessError as e: #error
        print(f"Error al ejecutar el comando: {e}")
    except FileNotFoundError: #en el caso de (no tener/tener dañado) systemctl
        print("Comando no encontrado. Asegúrate de tener 'systemctl' instalado.")

#Función para parar contenedores (por defecto se ejecutan y después se paran)
def parar_contenedor(parar_contenedor):
    #Lista los contenedores en el equipo
    containers = client.containers.list(all=True)
    #Variable de control
    container_exists = False

    #Bucle que recorre los contenedores listados en el equipo
    for container in containers:
        #condicion que analiza la variable pasada a la función funcion(variable)
        if container.name == parar_contenedor:
            container_exists = True #Variable de control
            container_to_stop = container #Buelca en la variable container_to_stop el contenedor a parar
            break #Sale del bucle
    if container_exists: #TRUE
        print(f"Contenedor '{parar_contenedor}' encontrado, deteniéndolo.")
        container_to_stop.stop()  # Detener el contenedor si está en ejecución usando .stop()
        print(f"Contenedor '{parar_contenedor}' detenido.")
    else: #FALSE
        print(f"El contenedor '{parar_contenedor}' no existe.")

#Función que sirve para reanudar contenedor, funciona igual que parar_contenedor()
def continuar_contenedor(continuar_contenedor):
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
        container_to_continue.start()  #Reanudar contenedor
        print(f"Contenedor '{continuar_contenedor}' reanuado.")
    else:
        print(f"El contenedor '{continuar_contenedor}' no existe.")


#función para eliminar contenedores
#Esta función no se usa en la gran mayoría de casos, ya que usando la herramienta PORTAINER se pueden eliminar los contenedores, solo see usará si el usuario lo especifica (por parámetro) junto a la acción de lanzar el script
#Funciona al igual que parar_contenedor o continuar_contenedor
def eliminar_contenedor(nombre_contenedor):
    try:
        # Obtener todos los contenedores 
        containers = client.containers.list(all=True)

        # Inicializar la variable que indicará si el contenedor existe
        container_exists = False
        container_to_remove = None

        for container in containers:
            if container.name == nombre_contenedor:
                container_exists = True
                container_to_remove = container
                break  # Salimos del bucle si encontramos el contenedor

        # Si el contenedor existe, detenerlo y eliminarlo
        if container_exists:
            print(f"Contenedor '{nombre_contenedor}' encontrado. Deteniéndolo y eliminándolo.")
            container_to_remove.stop()  # Detener el contenedor si está en ejecución
            container_to_remove.remove()  # Eliminar el contenedor (.remove())
            print(f"Contenedor '{nombre_contenedor}' detenido y eliminado.")
        else:
            print(f"El contenedor '{nombre_contenedor}' no existe.")
    
    except Exception as e: #error
        print(f"Error inesperado: {e}")


#Función para crear red en docker
#Creo todos los contenedores dentro de esta red virtual para asignarles IPs fijas
def crear_red():
    try:
        # Comprobar si la red ya existe
        redes_existentes = client.networks.list(names=["red"])
        if redes_existentes: #si hay alguna red con el nombre "red"
            print("La red 'red' ya existe.")
        else: #si no hay
            # Crear la red con la subred especificada
            red = client.networks.create(
                "red",        # Nombre de la red
                driver="bridge",   # Adaptador
                ipam=docker.types.IPAMConfig( #configuración
                    pool_configs=[docker.types.IPAMPool( #Red
                        subnet="192.168.250.0/24",  # Subred especificada
                    )]
                )
            )

            print(f"Red creada exitosamente con el driver 'bridge' y subnet '192.168.250.0/24'")
    
    except docker.errors.APIError as e: #error
        print(f"Error al crear la red: {e}")

#Contenedor con apache
def apacheserver():
    eliminar_contenedor("apache") #Si existe lo elimina

    # Ruta adicional
    htdocs = "/config/apache/htdocs"
    html = os.path.join(current_directory, htdocs.lstrip('/'))  # Unir las rutas

    try:
        container = client.containers.run(
            "php:7.4-apache", #imagen
            name="apache",
            network="red", #red (es obligatorio especificarla aunque se especifique con network_config más adelante)
            detach=True, #segundo plano
            volumes={html: {"bind": "/var/www/html", "mode": "rw"}}, #voluumen que monta el archivo index.html
            ports={'80/tcp': 80}, #puerto 80
            # Configuración especial para IP fija
            networking_config={
                'red': client.api.create_endpoint_config(
                    ipv4_address="192.168.250.10" #ip fija
                )
            }
        )
        print("Contenedor apache ejecutándose. Accede a http://localhost o  ejemploanxo.com en tu navegador.")
    except docker.errors.APIError as e: #error
        print(f"Error al crear el contenedor: {e}")

#Contenedor con bind9
def bind9server():
    #Carpetas de configuración
    dirconf = "/config/bind9/conf"
    conf_bind9_ruta = os.path.join(current_directory, dirconf.lstrip('/'))  # Unir las rutas
    dirzonas = "/config/bind9/zonas"
    zonas_bind9_ruta = os.path.join(current_directory, dirzonas.lstrip('/'))

    eliminar_contenedor("bind9") #eliminar contenedor
    try:
        container = client.containers.run(
            "ubuntu/bind9", #imagen
            name="bind9",
            network="red", #red
            detach=True, #segundo plano
            volumes={conf_bind9_ruta: {"bind": "/etc/bind", "mode": "ro"}, #/etc/bind
                    zonas_bind9_ruta: {"bind": "/var/lib/bind", "mode": "rw"}}, #/var/lib/bind
            ports={'53/tcp': 53, "53/udp": 53}, #puerto 53, entraría en conflicto con systemd-resolved pero cuando se lanza el contenedor más adelante se usa la función parar_systemresolved()
            networking_config={
                'red': client.api.create_endpoint_config(
                    ipv4_address="192.168.250.20" #ip fija
                )
            }
        )
        print("Contenedor bind9 ejecutándose.")
    except docker.errors.APIError as e: #errores
        print(f"Error al crear el contenedor: {e}")

#contenedor con samba
def samba():
    #Carpetas
    compartido = "/config/samba/compartido" #carpeta a compartir
    dircompartido = os.path.join(current_directory, compartido.lstrip('/'))
    confsmb = "/config/samba/config" #directorio configuración
    dirconfigsamba = os.path.join(current_directory, confsmb.lstrip('/'))

    eliminar_contenedor("samba")

    try:
        container = client.containers.run(
            "dperson/samba", #imagen
            name="samba",
            network="red", #red
            detach=True, #segundo plano
            volumes={dirconfigsamba: {"bind": "/etc/samba", "mode": "rw"}, #/etc/samba
                    dircompartido: {"bind": "/mnt/compartido", "mode": "rw"}}, #/mnt/compartido
            ports={'139/tcp': 139, '445/tcp': 445},
            networking_config={
                'red': client.api.create_endpoint_config(
                    ipv4_address="192.168.250.30" #ipfija
                )
            }
        )
        print("Contenedor samba ejecutándose.")
    except docker.errors.APIError as e: #error
        print(f"Error al crear el contenedor: {e}")

#Contenedor con mysql
def mysql():
    try:
        #Carpetas
        eliminar_contenedor("mysql")#eliminar contenedor

        dir_data="/config/mysql/data"
        data=os.path.join(current_directory, dir_data.lstrip('/')) #Datos
        #IMPORTANTE en ./config/mysql/conf/my.cnf incluir "bind-address = 0.0.0.0" para permitir el acceso remoto (y además poderlo usar con phpmyadmin)
        dir_cnf="/config/mysql/cnf"
        cnf=os.path.join(current_directory,dir_cnf.lstrip('/')) #Configuración

        container = client.containers.run(
        "mysql:latest",  # Usar la imagen oficial de MySQL
        name="mysql",
        environment={
            "MYSQL_ROOT_PASSWORD": "123456",
            "MYSQL_ROOT_HOST": "%"
            },
        volumes={data: {"bind": "/var/lib/mysql", "mode": "rw"}, #/var/lib/mysql
                cnf: {"bind": "/etc/mysql", "mode": "rw"}}, #/etc/mysql
        network="red", #red
        networking_config={
                'red': client.api.create_endpoint_config(
                    ipv4_address="192.168.250.40"
                )
            },
        ports={'3306/tcp': 3306},  # Exponer el puerto 3306
        detach=True,  # Ejecutar en segundo plano
        )
        print("Contenedor mysql ejecutándose.")
    except docker.errors.APIError as e: #errores
        print(f"Error al crear contenedor; {e}")

#Contenedor con phpmyadmin
#Para poder usar mysql de forma más gráfica uso phpmyadmin con el usuario admin y contraseña "123456"
#IMPORTANTE: El usuario admin ya fue creado, en el caso de borrar/modificar la carpeta "./config/mysql/data" se tendrá que acceder manualmente al contenedor mysql para crearlo 
#IMPORTANTE: si se modifica el contenedor de phpmyadmin para que use el usuario root no funcionará ya que no se permite el acceso de root de forma remota ('root'@'localhost')
#mysql -u root -p123456
#create user 'admin'@'%' IDENTIFIED BY '123456';
def phpmyadmin():
    try:
        eliminar_contenedor("phpmyadmin") #eliminar
        client.containers.run(
        "phpmyadmin:latest", #imagen
        name="phpmyadmin",
        environment={
            "PMA_HOST": "192.168.250.40",  # IP estática del contenedor MySQL
            "PMA_PORT": 3306,
            "PMA_USER": "admin", #usuario 'admin'@'%', no usar root
            "PMA_PASSWORD": "123456" #contraseña admin
        },
        network="red", #red
        networking_config={
                'red': client.api.create_endpoint_config(
                    ipv4_address="192.168.250.50" #ip fija
                )
            },
        ports={'80/tcp': 5000}, #puerto 5000, para que no colisione con el puerto 80 del contenedor apache
        detach=True, #segundo plano
    )
        print("Contenedor phpmyadmin ejecutandose")
    except Exception as e: #error
        print(f"Error al arrancar contenedor phpmyadmin: {e}")


#contenedor con ldap
def ldap(): 
    try:
        #Carpetas
        eliminar_contenedor("ldap")
        ldap_data="/config/ldap/data"
        ruta_ldap_data=os.path.join(current_directory,ldap_data.lstrip('/')) #Archivos
        ldap_conf="/config/ldap/conf"
        ruta_ldap_conf=os.path.join(current_directory,ldap_conf.lstrip('/')) #Configurración


        client.containers.run(
    "bitnami/openldap",#imagen
    name="ldap",
    ports={'389/tcp': 389, '636/tcp': 636}, #puertos
    network="red", #red
    networking_config={
                'red': client.api.create_endpoint_config(
                    ipv4_address="192.168.250.60" #ip fija
                )},
    volumes={
        ruta_ldap_conf: {'bind': '/opt/bitnami/openldap/etc', 'mode': 'rw'}, #/opt/bitnami/openldap/etc
        ruta_ldap_data: {'bind': '/bitnami/openldap', 'mode': 'rw'} #/bitnami/openldap
    },
    environment={
        'LDAP_ADMIN_PASSWORD': '123456', #contraseña admin
        'LDAP_ROOT': 'dc=ejemploanxo,dc=com' #dominio
    },
    command="tail -f /dev/null", #comando para que no se cierre el contenedor
    detach=True #segundo plano
    )
        print("Contenedor ldap ejecutandose")

    
    except Exception as e: #error
        print(f"Error al crear el contenedor ldap: {e}")

#Portainer
def portainer():
    eliminar_contenedor("portainer") #eliminar

    ruta_data="/config/portainer/data" 
    ruta_portainer_data=os.path.join(current_directory,ruta_data.lstrip('/')) #datos


    try:
        container = client.containers.run(
            "portainer/portainer-ce", #imagen
            name="portainer",
            ports={"9000/tcp": 5001}, #puerto
            #Para que el contenedor portainer pueda tener acceso a otros contenedores le monto el volumen con datos y el archivo local del equipo (/var/run/docker.sock)
            volumes={"/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "rw"}, #docker.sock
                    ruta_portainer_data: {"bind": "/data", "mode": "rw"}}, #datos
            restart_policy={"Name": "always"}, #controla cómo un contenedor debe reiniciarse si se detiene o si el sistema se reinicia.
            network="red", #red
            networking_config={
                'red': client.api.create_endpoint_config(
                    ipv4_address="192.168.250.70" #ip fija
                )
            },
            detach=True #segundo plano
        )
        print("Contenedor portainer ejecutandose")
    except docker.errors.APIError as e: #error
        print(f"Error al crear el contenedor {e}")    

# Verificar si el parámetro pasado es "samba"
if len(sys.argv) > 1 and sys.argv[1] == "--launch-samba":
    crear_red()
    samba()

elif len(sys.argv) > 1 and sys.argv[1] == "--stop-samba":
    parar_contenedor("samba")

elif len(sys.argv) > 1 and sys.argv[1] == "--continue-samba":
    continuar_contenedor("samba")

elif len(sys.argv) > 1 and sys.argv[1] == "--remove-samba":
    eliminar_contenedor("samba")

elif len(sys.argv) > 1 and sys.argv[1] == "--launch-apache":
    crear_red()
    apacheserver()

elif len(sys.argv) > 1 and sys.argv[1] == "--stop-apache":
    parar_contenedor("apache")

elif len(sys.argv) > 1 and sys.argv[1] == "--continue-apache":
    continuar_contenedor("apache")

elif len(sys.argv) > 1 and sys.argv[1] == "--remove-apache":
    eliminar_contenedor("apache")

elif len(sys.argv) > 1 and sys.argv[1] == "--launch-bind9":
    crear_red()
    parar_systemdresolved()
    bind9server()
   
elif len(sys.argv) > 1 and sys.argv[1] == "--stop-bind9":
    parar_contenedor("bind9")
    reanudar_systemdresolved()

elif len(sys.argv) > 1 and sys.argv[1] == "--continue-bind9":
    parar_systemdresolved()
    continuar_contenedor("bind9")

elif len(sys.argv) > 1 and sys.argv[1] == "--remove-bind9":
    eliminar_contenedor("bind9")
    reanudar_systemdresolved()

elif len(sys.argv) > 1 and sys.argv[1] == "--launch-mysql":
    crear_red()
    mysql()

elif len(sys.argv) > 1 and sys.argv[1] == "--stop-mysql":
    parar_contenedor("mysql")

elif len(sys.argv) > 1 and sys.argv[1] == "--continue-mysql":
    continuar_contenedor("mysql")

elif len(sys.argv) > 1 and sys.argv[1] == "--remove-mysql":
    eliminar_contenedor("mysql")


elif len(sys.argv) > 1 and sys.argv[1] == "--launch-phpmyadmin":
    crear_red()
    phpmyadmin()

elif len(sys.argv) > 1 and sys.argv[1] == "--stop-phpmyadmin":
    parar_contenedor("phpmyadmin")

elif len(sys.argv) > 1 and sys.argv[1] == "--continue-phpmyadmin":
    continuar_contenedor("phpmyadmin")

elif len(sys.argv) > 1 and sys.argv[1] == "--remove-phpmyadmin":
    eliminar_contenedor("phpmyadmin")

elif len(sys.argv) > 1 and sys.argv[1] == "--launch-ldap":
    crear_red()
    ldap()

elif len(sys.argv) > 1 and sys.argv[1] == "--stop-ldap":
    parar_contenedor("ldap")

elif len(sys.argv) > 1 and sys.argv[1] == "--continue-ldap":
    continuar_contenedor("ldap")

elif len(sys.argv) > 1 and sys.argv[1] == "--remove-ldap":
    eliminar_contenedor("ldap")

elif len(sys.argv) > 1 and sys.argv[1] == "--launch-portainer":
    crear_red()
    portainer()

elif len(sys.argv) > 1 and sys.argv[1] == "--stop-portainer":
    parar_contenedor("portainer")

elif len(sys.argv) > 1 and sys.argv[1] == "--continue-portainer":
    continuar_contenedor("portainer")

elif len(sys.argv) > 1 and sys.argv[1] == "--remove-portainer":
    eliminar_contenedor("portainer")

elif len(sys.argv) > 1 and sys.argv[1] == "--parar-systemdresolved":
    parar_systemdresolved()

elif len(sys.argv) > 1 and sys.argv[1] == "--reiniciar-systemdresolved":
    reanudar_systemdresolved()

elif len(sys.argv) > 1 and sys.argv[1] == "--help":
    print("Para lanzar este script es necesario usar sudo o root directamente.")
    print("El script creara los contenedores y los detendrá a todos menos al de portainer (localhost:5001) si se lanza sin parámetros.")
    print("Parámetros:")
    print("--launch-samba")
    print("--stop-samba")
    print("--continue-samba")
    print("--remove-samba")
    print("--launch-apache")
    print("--stop-apache")
    print("--continue-apache")
    print("--remove-apache")
    print("--launch-bind9")
    print("--stop-bind9")
    print("--continue-bind9")
    print("--remove-bind9")
    print("--launch-mysql")
    print("--stop-mysql")
    print("--continue-mysql")
    print("--remove-mysql")
    print("--launch-phpmyadmin")
    print("--stop-phpmyadmin")
    print("--continue-phpmyadmin")
    print("--remove-phpmyadmin")
    print("--launch-ldap")
    print("--stop-ldap")
    print("--continue-ldap")
    print("--remove-ldap")
    print("--launch-portainer")
    print("--stop-portainer")
    print("--continue-portainer")
    print("--remove-portainer")
    print("--parar-systemdresolved")
    print("--reiniciar-systemdresolved")
    print("--help")

else:
    #apache_local()
    crear_red()
    print("***********************************************************")
    apacheserver()
    parar_contenedor("apache")
    print("***********************************************************")
    parar_systemdresolved()
    bind9server()
    parar_contenedor("bind9")
    reanudar_systemdresolved()
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
    parar_contenedor("ldap")
    print("***********************************************************")
    print("admin, admin12345678")
    print("localhost:5001")
    portainer()
