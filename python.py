import docker
import os

# Crear el cliente Docker
client = docker.from_env()

# Ruta del archivo HTML en tu sistema local
html_file_path = "/home/anxo/Escritorio/proyecto/config/apache/htdocs/index.html"  # Cambia esta ruta a la ubicación de tu archivo HTML

# Verificar si el archivo existe
if not os.path.isfile(html_file_path):
    print(f"El archivo {html_file_path} no existe.")
else:
    # Crear el contenedor con la imagen "php:7.4-apache"
    # Montar el archivo HTML en el contenedor
    container = client.containers.run(
        "php:7.4-apache",
        volumes={html_file_path: {"bind": "/var/www/html/index.html", "mode": "ro"}},
        ports={'80/tcp': 80},
        detach=True
    )

    print("Contenedor ejecutándose, accede a http://localhost en tu navegador.")

