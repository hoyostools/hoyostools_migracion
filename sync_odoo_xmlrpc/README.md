# Sync Odoo XML-RPC (Sale Order)

Este módulo permite **sincronizar pedidos de venta (`sale.order`)** de una instancia Odoo hacia otra mediante **XML-RPC**.

---

## 🚀 Características
- Sincroniza pedidos de venta hacia una base remota.
- Evita duplicados con el campo `is_synced`.
- Busca el cliente remoto por **NIT/VAT** o por **nombre**. Si no existe, lo crea.
- Busca los productos por **default_code**. Si no existen, los crea.
- Envía las líneas del pedido y crea la orden en la base remota.
- Notificaciones amigables en la interfaz de Odoo.

---

## ⚙️ Configuración
En **Ajustes → Parámetros del sistema**, agrega:

- `sync_odoo_xmlrpc.remote_odoo_url` → URL del Odoo remoto (ejemplo: `https://mi-odoo-remoto.com`)
- `sync_odoo_xmlrpc.remote_odoo_db` → Nombre de la base remota
- `sync_odoo_xmlrpc.remote_odoo_user` → Usuario del Odoo remoto
- `sync_odoo_xmlrpc.remote_odoo_password` → Contraseña del usuario remoto

---

## 📖 Uso
1. Ir a **Ventas → Pedidos de venta**.
2. Abrir un pedido.
3. Pulsar el botón **Sincronizar Pedido**.
4. Verificar la notificación de éxito y el ID remoto creado.

---

## ✅ Requisitos
- Odoo 17 (compatible también con Odoo 16/18 con pequeños ajustes).
- Acceso remoto habilitado en la base destino con **XML-RPC**.

---

## 👨‍💻 Autor
**JMA**  
Integración de Odoo vía XML-RPC para sincronización de pedidos de venta.
