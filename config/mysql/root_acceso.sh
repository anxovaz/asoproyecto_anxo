#!/bin/bash

# Esperar activamente hasta que MySQL esté listo
echo "Esperando a que MySQL esté listo para aceptar conexiones..."
while ! mysql -h 127.0.0.1 -u root -p123456 -e "SELECT 1;" > /dev/null 2>&1; do
    echo "Esperando... MySQL no está listo"
    sleep 5
done

mysql -u root -p123456 -e "DROP USER 'admin'@'%';" 
mysql -u root -p123456 -e "CREATE USER 'admin'@'%' IDENTIFIED BY '123456';" 
mysql -u root -p123456 -e "GRANT ALL PRIVILEGES ON *.* TO 'admin'@'%' WITH GRANT OPTION;" 
mysql -u root -p123456 -e "FLUSH PRIVILEGES" 
echo "prueba">/mnt/a.txt
