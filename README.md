# Despliegue de Microservicios en Docker
Anxo Vázquez Lorenzo<br>
Proyecto final Administración Sistemas Operativos

## Descripción
Script en python que automáticamente desplega varios contenedores en docker con servicios "usuales" dentro de una red empresarial.<br>

Para este proyecto se usan las siguientes librerías en python:<br>
·docker<br>
·os<br>
·subprocess<br>
·sys<br>
·docker.errors<br>

Se crean los siguientes servicios usando contenedores:<br>
·WEB (APACHE)<br>
·DNS (BIND9)<br>
·SISTEMA GESTOR DE BASES DE DATOS (MYSQL Y PHPMYADMIN)<br>
·SISTEMA PARA COMPARRTIR ARCHIVOS (SAMBA)<br>
·SISTEMA DE DIRECTORIO ACTIVO (LDAP)<br>
·SISTEMA GESTOR DE CONTENEDORES (PORTAINER)<br>

## FINALIDAD 
La finalidad de este proyecto es crear un script en python que con tan solo ejecutarlo despliegue servicios útiles en una red empresarial pequeña.<br>
Para este proyecto uso contenedores devido a que son portables y que (en este proyecto) están principalmente orientados a ser ejecutados en un equipo normal de la empresa, si la empresa en algun comento quiere invertir en un servidor puede copiar los archivos de configuración de la carpeta ./config y no perder ninguna configuración de los contenedores.

## Accedo a las herramientas web
·Apache: localhost:80<br>
·Portainer: localhost:50001<br>
·PhpMyAdmin: localhost:5000<br>

## COMPATIBILIDAD
Se ha probado la compatibilidad de este proyecto en:<br>
·Ubuntu 20.04.6 LTS<br>

## Código
### docker.from_env()
Se utiliza para crear un cliente Docker que permite interactuar con el daemon de Docker.
```shell
client = docker.from_env()
```

### systemd-resolved
Uno de los problemas con el contenedor bind9 es que colisiona con el servicio systemd-resolved, para ello uso las siguientes funciones:
```shell
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

```
PD: El mensaje "sudo: imposible resolver el anfitrión vboxubuntu: Fallo temporal en la resolución del nombre" no indica ningún problema para el funcionamiento del script, este mensaje aparrece cuando se ejecuta una orden sudo con el servicio systemd-resolved parado.

### Red docker
Para asignar una ip fija a un contenedor en docker no vale con tan solo usar el campo "network", hay que usar la siguiente sentencia:

```shell
network="red",
networking_config={
                'red': client.api.create_endpoint_config(
                    ipv4_address="192.168.250.10" #ip fija
                )
            }
```

### Mysql y Phpmyadmin
Para poder gestionar de una forma más gráfica mysql uso phpmyadmin.<br>
Uno de los problemas fue la conexión de phpmyadmina a mysql ya que no podía usar el usuario root de mysql, para solucionarlo creé un usuario llamado "admin" con el campo "%" ('admin'@'%') para que se pudiese conectar desde cualquier equipo, además en el archivo my.cnf tiene que estar el campo "bind-address = 0.0.0.0".<br>
Usuario:
```shell
mysql -u root -p123456
create user 'admin'@'%' IDENTIFIED BY '123456';
```
my.cnf:
```shell
bind-address = 0.0.0.0
```
Otro problema fue conectar phpmyadmin con mysql, para ello uso "enviroment" indicando IP, puerto, usuario y contraseña.
```shell
 environment={
            "PMA_HOST": "192.168.250.40",  # IP estática del contenedor MySQL
            "PMA_PORT": 3306,
            "PMA_USER": "admin", #usuario 'admin'@'%', no usar root
            "PMA_PASSWORD": "123456" #contraseña admin
        },
```
### OpenLdap
El contenedor cada vez que se ponía en ejecución se cerraba sin mostrar ningún registro de error, para ello uso la siguiente sentencia para que no se cierre.
```shell
command="tail -f /dev/null",
```

### Portainer
El principal problema de este herramienta es entender como es capaz de interactuar con la máquina host, para ello es posible crear un volumen compartido entre máquina host y contenedor (/var/run/docker.sock").
```shell
 volumes={"/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "rw"}, #docker.sock
                    ruta_portainer_data: {"bind": "/data", "mode": "rw"}}, #datos
```

