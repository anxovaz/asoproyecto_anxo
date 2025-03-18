<?php
// samba.php

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
            case '--stop-samba':
                echo ejecutar_comando('python3 /var/python.py --stop-samba');
                break;
            case '--launch-samba':
                echo ejecutar_comando('python3 /var/python.py --launch-samba');
                break;
            case '--continue-samba':
                echo ejecutar_comando('python3 /var/python.py --continue-samba');
                break;
            case '--eliminar-samba':
                echo ejecutar_comando('python3 /var/python.py --eliminar-samba');
                break;
            default:
                echo "Acción no válida.";
        }
    }
}

// Enlace para volver a la página de inicio
echo '<a href="admin.html">Volver a la página de inicio</a>';
?>
