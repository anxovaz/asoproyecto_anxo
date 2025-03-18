<?php
// bind9.php

// Función para ejecutar comandos en el servidor de backend, como ejecutar scripts en Python
function ejecutar_comando($comando) {
    $output = shell_exec("sudo $comando");
    return $output;
}

// Verificar si se ha enviado una acción
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (isset($_POST['accion'])) {
        $accion = $_POST['accion'];

        // Comando dependiendo de la acción
        switch ($accion) {
            case '--stop-bind9':
                echo ejecutar_comando('python3 /mnt/python.py --stop-bind9');
                break;
            case '--launch-bind9':
                echo ejecutar_comando('python3 /mnt/python.py --launch-bind9');
                break;
            case '--continue-bind9':
                echo ejecutar_comando('python3 /mnt/python.py --continue-bind9');
                break;
            case '--eliminar-bind9':
                echo ejecutar_comando('python3 /mnt/python.py --eliminar-bind9');
                break;
            default:
                echo "Acción no válida.";
        }
    }
}


?>
<html>
    <head>
        <meta charset="utf8">
    </head>
    <body>
        <a href="admin.html">Volver a la página de inicio</a>
    </body>
</html>