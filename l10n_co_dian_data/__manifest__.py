# -*- coding: utf-8 -*-
{
    'name': "DIAN Data Fields",
    'summary': "Campos y catálogos requeridos por la DIAN para la localización colombiana.",
    'description': """
Este módulo proporciona estructuras y catálogos de datos necesarios para cumplir con los requisitos de la DIAN en Colombia.

Incluye:
- Responsabilidades fiscales (tax scheme y tax level code)
- Conceptos de corrección para notas crédito y débito
- Formas y medios de pago
- Grupos tributarios colombianos
- Datos de ubicación: ciudades, estados, países y códigos ZIP
- Tipos de persona y nombres separados en contactos
- Nombre comercial del socio
- Resoluciones de secuencia DIAN
- Códigos de unidad de medida colombianos
- Dirección y códigos CIIU para contactos
- Regímenes fiscales

Compatible con Odoo Localización Colombia.

""",
    'author': "Brawil Solutions Sas",
    'website': "",
    'category': 'Localization',
    'version': '0.1',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'base_setup',
        'base_vat',
        'product',
        'base_address_extended',
        'contacts',
    ],
    'data': [
        # Fiscal Position Party Tax Scheme
        "security/l10n_co_account_fiscal_position_party_tax_scheme/ir.model.access.csv",
        "data/l10n_co_account_fiscal_position_party_tax_scheme/account_fiscal_position_tax_level_code_data.xml",
        "data/l10n_co_account_fiscal_position_party_tax_scheme/account_fiscal_position_tax_scheme_data.xml",
        "views/l10n_co_account_fiscal_position_party_tax_scheme/account_fiscal_position_views.xml",

        # Invoice Discrepancy Response
        "security/l10n_co_account_invoice_discrepancy_response/ir.model.access.csv",
        "data/l10n_co_account_invoice_discrepancy_response/account_invoice_discrepancy_response_code_data.xml",
        "wizards/l10n_co_account_invoice_discrepancy_response/account_invoice_debit_note.xml",
        "wizards/l10n_co_account_invoice_discrepancy_response/account_invoice_refund.xml",
        "views/l10n_co_account_invoice_discrepancy_response/account_invoice_views.xml",
        "views/l10n_co_account_invoice_discrepancy_response/account_journal_views.xml",

        # Payment Mean
        "security/l10n_co_account_invoice_payment_mean/ir.model.access.csv",
        "data/l10n_co_account_invoice_payment_mean/account_payment_mean_data.xml",
        "data/l10n_co_account_invoice_payment_mean/account_payment_mean_code_data.xml",
        "views/l10n_co_account_invoice_payment_mean/account_invoice_views.xml",

        # Tax Group Type
        "security/l10n_co_account_tax_group_type/ir.model.access.csv",
        "data/l10n_co_account_tax_group_type/account_tax_group_type_data.xml",
        "views/l10n_co_account_tax_group_type/account_tax_group_views.xml",

        # Base Location (Ciudades, ZIPs, Departamentos)
        "security/l10n_co_base_location/ir.model.access.csv",
        "data/l10n_co_base_location/res_country_data.xml",
        "data/l10n_co_base_location/res_country_state_data.xml",
        "data/l10n_co_base_location/res_city_data.xml",
        "data/l10n_co_base_location/res_city_zip_data.xml",
        "views/l10n_co_base_location/res_city_zip_view.xml",
        "views/l10n_co_base_location/res_city_view.xml",
        "views/l10n_co_base_location/res_company_view.xml",
        "views/l10n_co_base_location/res_partner_view.xml",

        # Partner - Persona natural o jurídica
        "views/l10n_co_partner_person_type/res_config_settings_views.xml",
        "views/l10n_co_partner_person_type/res_partner_views.xml",
        "views/l10n_co_partner_person_type/res_users_views.xml",

        # Partner VAT
        "security/l10n_co_partner_vat/ir.model.access.csv",
        "data/l10n_co_partner_vat/res_partner_document_type_data.xml",
        "views/l10n_co_partner_vat/res_partner_views.xml",

        # Secuencia DIAN
        "views/l10n_co_sequence_resolution/ir_sequence_views.xml",
        "views/l10n_co_sequence_resolution/account_invoice_views.xml",

        # Nombre comercial
        "views/partner_commercial_name/res_partner_views.xml",

        # Fiscal position list name
        "views/l10n_co_account_fiscal_position_listname/account_fiscal_position_views.xml",

        # Unidades de medida colombianas
        "security/l10n_co_product_uom/ir.model.access.csv",
        "data/l10n_co_product_uom/product.uom.code.csv",
        "views/l10n_co_product_uom/product_uom_views.xml",

        # Dirección, códigos CIIU y nomenclatura
        "security/partner_address_ciiu/ir.model.access.csv",
        "data/partner_address_ciiu/address_code_data.xml",
        "data/partner_address_ciiu/street_code_data.xml",
        "views/partner_address_ciiu/address_code_views.xml",
        "views/partner_address_ciiu/ciiu_value_views.xml",
        "views/partner_address_ciiu/street_code_views.xml",
        "views/partner_address_ciiu/res_partner_views.xml",
    ],
    # 'post_init_hook': 'post_init_hook'
}
