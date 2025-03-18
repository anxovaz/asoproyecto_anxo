<?php
// apache.php

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
            case '--stop-apache':
                echo ejecutar_comando('python3 /var/python.py --stop-apache');
                break;
            case '--launch-apache':
                echo ejecutar_comando('python3 /var/python.py --launch-apache');
                break;
            case '--continue-apache':
                echo ejecutar_comando('python3 /var/python.py --continue-apache');
                break;
            case '--eliminar-apache':
                echo ejecutar_comando('python3 /var/python.py --eliminar-apache');
                break;
            default:
                echo "Acción no válida.";
        }
    }
}

// Enlace para volver a la página de inicio
echo '<a href="admin.html">Volver a la página de inicio</a>';
?>
