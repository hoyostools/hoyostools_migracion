# -*- coding: utf-8 -*-
{
    "name": "Cloud Storage Solutions",
    "version": "17.0.1.4.40",
    "category": "Document Management",
    "author": "faOtools",
    "website": "https://faotools.com/apps/17.0/cloud-storage-solutions-17-0-cloud-base-836",
    "license": "Other proprietary",
    "application": True,
    "installable": True,
    "auto_install": False,
    "depends": [
        "portal"
    ],
    "data": [
        "security/security.xml",
        "data/data.xml",
        "data/mail_data.xml",
        "data/cron.xml",
        "data/mass_actions.xml",
        "security/ir.model.access.csv",
        "views/clouds_log.xml",
        "views/sync_model.xml",
        "views/clouds_client.xml",
        "views/ir_attachment.xml",
        "views/clouds_folder.xml",
        "views/clouds_queue.xml",
        "views/clouds_tag.xml",
        "wizard/share_send_invitation.xml",
        "views/clouds_share.xml",
        "views/res_config_settings.xml",
        "wizard/mass_attachment_update.xml",
        "wizard/mass_update_tag.xml",
        "wizard/mass_create_share.xml",
        "wizard/mail_compose_message.xml",
        "wizard/compose_choose_attachments.xml",
        "wizard/add_url_attachment.xml",
        "views/menu.xml",
        "views/templates.xml",
        "views/photos_slideshow.xml"
    ],
    "assets": {
        "cloud_base.slider": [
                "cloud_base/static/src/components/photos_slideshow/*.xml",
                "cloud_base/static/src/components/photos_slideshow/*.js",
                "cloud_base/static/src/components/photos_slideshow/*.scss"
        ],
        "web.assets_backend": [
                "cloud_base/static/src/views/kanban/*.scss",
                "cloud_base/static/src/views/kanban/*.xml",
                "cloud_base/static/src/views/kanban/*.js",
                "cloud_base/static/src/views/search/*.js",
                "cloud_base/static/src/views/list/*.js",
                "cloud_base/static/src/views/fields/jstree_widget/*.xml",
                "cloud_base/static/src/views/fields/jstree_widget/*.js",
                "cloud_base/static/src/views/fields/rule_parent/*.xml",
                "cloud_base/static/src/views/fields/rule_parent/*.js",
                "cloud_base/static/src/views/fields/attachments_search/*.js",
                "cloud_base/static/src/views/fields/attachments_many2many/*.js",
                "cloud_base/static/src/views/fields/attachments_many2many/*.xml",
                "cloud_base/static/src/components/cloud_manager/*.xml",
                "cloud_base/static/src/components/cloud_manager/*.js",
                "cloud_base/static/src/components/cloud_jstree_container/*.xml",
                "cloud_base/static/src/components/cloud_jstree_container/*.js",
                "cloud_base/static/src/components/node_jstree_container/*.xml",
                "cloud_base/static/src/components/node_jstree_container/*.js",
                "cloud_base/static/src/components/cloud_navigation/*.xml",
                "cloud_base/static/src/components/cloud_navigation/*.js",
                "cloud_base/static/src/components/cloud_logs/*.xml",
                "cloud_base/static/src/components/cloud_logs/*.js",
                "cloud_base/static/src/components/cloud_logs/*.scss",
                "cloud_base/static/src/components/cloud_upload_zone/*.xml",
                "cloud_base/static/src/components/cloud_upload_zone/*.js",
                "cloud_base/static/src/components/cloud_upload_zone/*.scss",
                "cloud_base/static/src/core/common/*.js",
                "cloud_base/static/src/core/common/*.xml",
                "cloud_base/static/src/core/common/*.scss",
                "cloud_base/static/src/core/web/*.js",
                "cloud_base/static/src/core/web/*.xml",
                "cloud_base/static/src/components/photos_slideshow_action/*.xml",
                "cloud_base/static/src/components/photos_slideshow_action/*.js",
                [
                        "include",
                        "cloud_base.slider"
                ]
        ],
        "web.assets_frontend": [
                "cloud_base/static/src/portal/*.scss",
                "cloud_base/static/src/portal/*.js",
                "cloud_base/static/src/components/cloud_upload_zone/cloud_upload_zone.scss",
                "cloud_base/static/src/views/kanban/cloud_manager_search.scss",
                [
                        "include",
                        "cloud_base.slider"
                ]
        ]
},
    "demo": [
        
    ],
    "external_dependencies": {
        "python": [
                "sortedcontainers"
        ]
},
    "summary": "The tool to flexibly structure Odoo attachments in folders and synchronize directories with cloud clients: Google Drive, OneDrive/SharePoint, Nextcloud/ownCloud, and Dropbox. DMS. File Manager. Document management system. Attachments cloud base. Attachments manager. Two way integration. Files Sharing. Share files. Share folders. Share directories. Attachment tags. Attachments tags. Bilateral synchronization. Attachment manager. Cloud services.",
    "description": """
For the full details look at static/description/index.html
* Features *- Odoo File Manager Interface- Enhanced Attachment Box- Cloud Storage Synchronization- &lt;span id=&#34;cloud_base_folder_rules&#34;&gt;Automatic Folder Structure&lt;/span&gt;- Files and Folders Sharing- Document Management and Sync Access Rights- Use Notes
#odootools_proprietary""",
    "images": [
        "static/description/main.png"
    ],
    "price": "398.0",
    "currency": "EUR",
    "live_test_url": "https://faotools.com/my/tickets/newticket?&url_app_id=11&ticket_version=17.0&url_type_id=3",
}