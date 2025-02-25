import docker
import os
import time

# Crear el cliente Docker
client = docker.from_env()

# Ruta del archivo HTML en tu sistema local
current_directory = os.path.dirname(os.path.abspath(__file__))
print(f"El directorio actual del script es: {current_directory}")

# Ruta adicional
additional_path = "/config/apache/htdocs/index.html"
html_file_path = os.path.join(current_directory, additional_path.lstrip('/'))  # Unir las rutas

print(f"El directorio completo es: {html_file_path}")

# Verificar si el archivo existe
if not os.path.isfile(html_file_path):
    print(f"El archivo {html_file_path} no existe.")
else:
    container_name = "apache"

    # Obtener la lista de contenedores en ejecución (todos, incluyendo detenidos)
    containers = client.containers.list(all=True)

    # Comprobar si el contenedor llamado "apache" existe
    container_exists = False
    for container in containers:
        if container.name == container_name:
            container_exists = True
            break

    # Si el contenedor existe, detenerlo y eliminarlo
    if container_exists:
        print(f"Contenedor {container_name} encontrado. Deteniéndolo y eliminándolo.")
        container.stop()  # Detener el contenedor
        container.remove()  # Eliminar el contenedor
        print(f"Contenedor {container_name} detenido y eliminado.")
    else:
        print(f"El contenedor {container_name} no existe.")

    # Crear el contenedor con la imagen "php:7.4-apache"
    # Montar el archivo HTML en el contenedor
    try:
        container = client.containers.run(
            "php:7.4-apache",
            name=container_name,  # Asignar un nombre único al contenedor
            volumes={html_file_path: {"bind": "/var/www/html/index.html", "mode": "ro"}},
            ports={'80/tcp': 80},  # Exponer el puerto 80
            detach=True           # Ejecuta el contenedor en segundo plano
        )
        print(f"Contenedor {container_name} ejecutándose. Accede a http://localhost en tu navegador.")
    except docker.errors.APIError as e:
        print(f"Error al crear el contenedor: {e}")
