# Purchase to Sale Sync

Este módulo permite que, al crear una orden de compra en una instancia de Odoo, se genere automáticamente una orden de venta en otra instancia Odoo remota mediante XML-RPC. Es ideal para flujos de integración entre empresas proveedor-cliente usando Odoo.

## ✅ Funcionalidades

- Sincroniza automáticamente una orden de compra como una orden de venta.
- Conexión segura a otra instancia Odoo mediante XML-RPC.
- Búsqueda de productos por `default_code`.
- Búsqueda y creación automática de cliente remoto.
- Configuración de parámetros de conexión desde Ajustes Generales.

## ⚙️ Requisitos

- Odoo 17+
- Acceso a la otra instancia Odoo vía XML-RPC
- Los productos deben tener asignado un `default_code` para que se sincronicen correctamente.

## 🧩 Instalación

1. Copia el módulo en tu carpeta de addons personalizada.
2. Instala el módulo desde el backend de Odoo.
3. Ve a **Ajustes > Configuración General** y llena los siguientes campos:
   - URL de Odoo remoto
   - Base de datos remota
   - Usuario remoto
   - Contraseña remota

## 🔄 Flujo de trabajo

1. Un usuario crea una orden de compra en Odoo A.
2. El módulo automáticamente:
   - Se conecta a Odoo B.
   - Verifica si el cliente existe, lo crea si no.
   - Busca los productos por su `default_code`.
   - Crea una orden de venta con las líneas correspondientes.
3. Se registra un `note` indicando que fue generado automáticamente.

## 🛠️ Personalización

Puedes extender el módulo para:
- Crear productos automáticamente si no existen.
- Reintentar sincronización manualmente.
- Sincronizar solo órdenes de ciertas compañías o proveedores.
