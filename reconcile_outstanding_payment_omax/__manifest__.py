# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Reconcile Outstanding Payment with Invoices, Bills, Credit Notes, Refunds',
    'version': '1.0',
    'category': 'Accounting,Sales,Purchases,Productivity',
    'sequence': 1,
    'author': 'OMAX Informatics',
    'website': 'https://www.omaxinformatics.com',
    'description' : '''
        This Odoo app helps Accountants to do multiple reconcile outstanding Payments against with multiple Invoices, Credit Notes, Bills, Refunds in the same Wizard/Pop Up. It's also allow to reconcile invoices with credit notes and vice versa & Bills with Refunds and vice versa.
    ''',
    'depends' : ['account'],
    'data': [
        'security/ir.model.access.csv',
        'security/group.xml',
        'wizard/outstanding_payment.xml',
        'wizard/payment_allocation.xml',
        'views/account_payment.xml',
    ],
    'demo': [],
    'test': [],
    'images': ['static/description/banner.png',],
    'license': 'OPL-1',
    'currency':'USD',
    'price': 60,
    'installable' : True,
    'auto_install' : False,
    'application' : True,
    'pre_init_hook': 'pre_init_check',
    'module_type': 'official',
    'summary': '''
        Reconcilation multiple reconcile outstanding Payments against with multiple Invoices, Credit Notes, Bills, Refunds in the same Wizard/Pop Up.
        adjust multiple Invoices against with multiple Outstanding Payments
        adjust multiple Outstanding Debits against with multiple Customer Credit Notes.
        Multiple Vendor Bills reconcile with Outstanding debits.
        Multiple Refunds reconcile with related Outstanding credits.
        Reconcile invoice Payments Reconcile bill Payments Reconciliation process in Invoices
        Multiple Reconcile invoices Reconciliation Multiple Reconcile bills Reconciliation Multiple Reconcile credit notes Reconciliation Multiple Reconcile refunds Reconciliation Multiple Reconcile receipts Reconciliation
        Reconcile customer payments Reconcile vendor payments Reconcile customer credit note Reconcile vendor credit note Reconcile 
        Reconcile Outstanding Credits to invoices Reconcile invoices to Outstanding Credits Reconcile Outstanding debits to credit notes Reconcile Customer credit notes Reconcile Credit note to bills Reconcile Outstanding debits Reconcile Outstanding Bills Reconcile Payments Reconcile Outstanding Payment in Invoices, Reconcile Outstanding Payment in credit Notes Reconcile Outstanding Payment in Bills Reconcile Outstanding Payment in REFUNDS Reconcile Outstanding Payment in vendor credit note advance payment Reconcile advance payment Reconciliation advance customer payment reconcile advance vendor payment reconcile
        mass reconciliation in invoice mass reconciliation in bills mass reconciliation in credit notes mass reconciliation in refunds mass reconciliation in   receipts mass reconcile in invoice mass reconcile in bills mass reconcile in credit notes mass reconcile in refunds mass reconcile in receipts 
        partial reconciliation in invoice partial reconciliation in bill partial reconciliation in credit note partial reconciliation in refunds partial reconciliation in receipts partial Reconcile in invoice partial Reconcile in bill partial Reconcile in credit note partial Reconcile in refunds partial Reconcile in receipts partial reconciliation outstanding Payments partial reconciliation outstanding credits partial reconciliation outstanding debits partial reconciliation  payments Reconcile invoice to payments Reconcile invoice to credit notes Reconcile invoice to customer payment Reconcile invoice to customer credit notes Reconcile bills to payments Reconcile bill to vendor payments Reconcile bill to refunds Reconcile bill to vendor credit notes reconcile invoices with credit notes reconcile Bills with Refunds Reconcile selected payments with invoices payment allocation.
French
-------
plusieurs rapprochements des paiements impayés avec plusieurs factures, notes de crédit, factures et remboursements dans le même assistant/pop-up.
         ajuster plusieurs factures avec plusieurs paiements impayés
         ajuster plusieurs débits impayés avec plusieurs notes de crédit client.
         Les factures de plusieurs fournisseurs sont rapprochées des débits impayés.
         Les remboursements multiples sont rapprochés des crédits en cours associés.
         Rapprocher les paiements des factures Rapprocher les paiements des factures Processus de rapprochement dans les factures
         Rapprochement multiple des factures Rapprochement Rapprochement multiple des factures Rapprochement Rapprochement multiple des notes de crédit Rapprochement Rapprochement multiple des remboursements Rapprochement Rapprochement multiple des reçus Rapprochement
         Rapprocher les paiements clients Rapprocher les paiements fournisseur Rapprocher la note de crédit client Rapprocher la note de crédit fournisseur Rapprocher
         Rapprocher les crédits impayés avec les factures Rapprocher les factures avec les crédits impayés Rapprocher les débits impayés avec les notes de crédit Rapprocher les notes de crédit des clients Rapprocher la note de crédit avec les factures Rapprocher les débits impayés Rapprocher les factures impayées Rapprocher les paiements Rapprocher les paiements impayés dans les factures, Rapprocher les paiements impayés dans les notes de crédit Rapprocher les paiements impayés dans les factures Rapprocher les paiements impayés dans REFUNDS Rapprocher les paiements impayés dans la note de crédit du fournisseur, paiement anticipé Rapprocher le paiement anticipé Rapprochement paiement anticipé du client, rapprocher le paiement anticipé du fournisseur, rapprocher
         rapprochement en masse dans la facture rapprochement en masse dans les factures rapprochement en masse dans les notes de crédit rapprochement en masse dans les remboursements rapprochement en masse dans les reçus rapprochement en masse dans la facture rapprochement en masse dans les factures rapprochement en masse dans les notes de crédit rapprochement en masse dans les remboursements rapprochement en masse dans les reçus
         rapprochement partiel dans la facture rapprochement partiel dans la facture rapprochement partiel dans la note de crédit rapprochement partiel dans les remboursements rapprochement partiel dans les reçus partiel Rapprochement dans la facture partiel Rapprochement dans la facture partiel Rapprochement dans la note de crédit partiel Rapprochement dans les remboursements partiel Rapprochement dans les reçus rapprochement partiel en cours Paiements rapprochement partiel crédits en cours rapprochement partiel des débits impayés rapprochement partiel des paiements Rapprocher la facture avec les paiements Rapprocher la facture avec les notes de crédit Rapprocher la facture avec le paiement du client Rapprocher la facture avec les notes de crédit du client Rapprocher les factures avec les paiements Rapprocher la facture avec les paiements du fournisseur Rapprocher la facture avec les remboursements Rapprocher la facture avec les notes de crédit du fournisseur rapprocher les factures avec le crédit les notes rapprochent les factures avec les remboursements Rapprochez les paiements sélectionnés avec l'allocation des paiements des factures.
Spanish
-------
conciliar múltiples pagos pendientes con múltiples facturas, notas de crédito, facturas y reembolsos en el mismo asistente/ventana emergente.
         ajustar múltiples facturas con múltiples pagos pendientes
         ajuste múltiples débitos pendientes con múltiples notas de crédito del cliente.
         Varias facturas de proveedores se concilian con los débitos pendientes.
         Múltiples reembolsos se concilian con créditos pendientes relacionados.
         Conciliar factura Pagos Conciliar factura Pagos Proceso de conciliación en Facturas
         Conciliación de facturas múltiples Conciliación de facturas de conciliación múltiple Conciliación de notas de crédito de conciliación múltiple Conciliación de reembolsos de conciliación múltiple Conciliación de recibos de conciliación múltiple
         Conciliar pagos de clientes Conciliar pagos de proveedores Conciliar nota de crédito de cliente Conciliar nota de crédito de proveedor Conciliar
         Conciliar créditos pendientes con facturas Conciliar facturas con créditos pendientes Conciliar débitos pendientes con notas de crédito Conciliar notas de crédito de clientes Conciliar nota de crédito con facturas Conciliar débitos pendientes Conciliar facturas pendientes Conciliar pagos Conciliar pagos pendientes en facturas, Conciliar pagos pendientes en notas de crédito Conciliar pagos pendientes en facturas Conciliar el pago pendiente en REEMBOLSOS Conciliar el pago pendiente en la nota de crédito del proveedor pago por adelantado Conciliar el pago por adelantado Conciliar el pago por adelantado del cliente conciliar el pago por adelantado al proveedor conciliar
         conciliación masiva en factura conciliación masiva en facturas conciliación masiva en notas de crédito conciliación masiva en reembolsos conciliación masiva en recibos conciliación masiva en factura conciliación masiva en facturas conciliación masiva en notas de crédito conciliación masiva en reembolsos conciliación masiva en recibos
         Conciliación parcial en factura Conciliación parcial en factura Conciliación parcial en nota de crédito Conciliación parcial en devoluciones Conciliación parcial en recibos parcial Conciliación en factura parcial Conciliación en factura parcial Conciliación en nota de crédito parcial Conciliación en devoluciones parciales Conciliación en recibos Conciliación parcial pendiente Pagos conciliación parcial créditos pendientes conciliación parcial débitos pendientes conciliación parcial pagos Conciliar factura con pagos Conciliar factura con notas de crédito Conciliar factura con pago del cliente Conciliar factura con notas de crédito del cliente Conciliar factura con pagos Conciliar factura con pagos de proveedor Conciliar factura con reembolsos Conciliar factura con notas de crédito de proveedor conciliar facturas con crédito notas conciliar facturas con reembolsos Conciliar pagos seleccionados con la asignación de pagos de facturas.
Chinese
-------
在同一个向导/弹出窗口中对多个发票、贷方票据、账单、退款的未付款项进行多次核对。
         根据多笔未付款项调整多张发票
         根据多个客户贷项票据调整多个未清借项。
         多个供应商账单与未清借项进行核对。
         多次退款与相关的未偿还积分一致。
         核对发票付款 核对帐单付款 发票中的核对流程
         多重调节发票 调节 多重调节账单 调节 多重调节贷方票据 调节 多重调节退款 调节 多重调节收据调节
         调节客户付款 调节供应商付款 调节客户贷方票据 调节供应商贷方票据 调节
         调节未清贷项与发票 调节发票与未清贷项 调节未清借项与贷项票据 调节客户贷项票据 调节贷项票据与账单 调节未偿借项 调节未偿账单 调节付款 调节发票中的未偿付款，调节贷项票据中的未偿付款 调节账单中的未偿付款 调节退款中的未付款项 调节供应商贷方票据预付款中的未付款项 调节预付款 调节预付款客户付款 调节预付款供应商付款调节
         发票中的批量调节 票据中的批量调节 贷方票据中的批量调节 退款中的批量调节 收据中的批量调节 发票中的批量调节 票据中的批量调节 贷方票据中的批量调节 退款中的批量调节 收据中的批量调节
         发票部分调节 账单部分调节 贷项通知单部分调节 退款部分调节 收款部分调节 部分发票调节 账单部分调节 贷项通知单部分调节 退款部分调节 收款部分调节 未清付款 部分调节 未清贷项 部分对账 未清借方 部分对账付款 调节发票与付款 调节发票与贷方票据 调节发票与客户付款 调节发票与客户贷方票据 调节账单与付款 调节账单与供应商付款 调节账单与退款 调节账单与供应商贷方票据 调节发票与贷方 注释 核对账单与退款 将选定的付款与发票付款分配进行核对。
German
-----
Mehrere ausstehende Zahlungen mit mehreren Rechnungen, Gutschriften, Rechnungen und Rückerstattungen im selben Assistenten/Popup abgleichen.
         Passen Sie mehrere Rechnungen mit mehreren ausstehenden Zahlungen an
         Mehrere ausstehende Belastungen mit mehreren Kundengutschriften ausgleichen.
         Mehrere Kreditorenrechnungen werden mit ausstehenden Belastungen abgeglichen.
         Mehrere Rückerstattungen werden mit den entsprechenden ausstehenden Gutschriften abgeglichen.
         Rechnungszahlungen abgleichen Rechnungszahlungen abgleichen Abstimmungsprozess in Rechnungen
         Mehrere Rechnungen abgleichen, Rechnungen abgleichen, Rechnungen mehrfach abgleichen, Gutschriften mehrfach abgleichen, Rückerstattungen mehrfach abgleichen, Quittungen mehrfach abgleichen, Abgleich
         Kundenzahlungen abgleichen, Lieferantenzahlungen abgleichen, Kundengutschrift abgleichen, Kreditorengutschrift abgleichen. Abgleichen
         Ausstehende Gutschriften mit Rechnungen abgleichen, Rechnungen mit ausstehenden Gutschriften abgleichen, ausstehende Belastungen mit Gutschriften abgleichen, Kundengutschriften abgleichen, Gutschriften mit Rechnungen abgleichen, ausstehende Belastungen abgleichen, ausstehende Rechnungen abgleichen, Zahlungen abgleichen, ausstehende Zahlungen in Rechnungen abgleichen, ausstehende Zahlungen in Gutschriften abgleichen, ausstehende Zahlungen in Rechnungen abgleichen Ausstehende Zahlung in RÜCKERSTATTUNGEN abgleichen. Ausstehende Zahlung in der Vorauszahlung der Kreditorengutschrift abgleichen. Vorauszahlung abgleichen. Kundenvorauszahlung abgleichen. Kreditorenvorauszahlung abgleichen
         Massenabstimmung in Rechnungen, Massenabstimmung in Rechnungen, Massenabstimmung in Gutschriften, Massenabstimmung in Erstattungen, Massenabstimmung in Belegen, Massenabstimmung in Rechnungen, Massenabstimmung in Rechnungen, Massenabstimmung in Gutschriften, Massenabstimmung in Rückerstattungen, Massenabstimmung in Belegen
         teilweiser Abgleich in der Rechnung, teilweiser Abgleich in der Rechnung, teilweiser Abgleich in der Gutschrift, teilweiser Abgleich in Erstattungen, teilweiser Abgleich in Belegen, teilweiser Abgleich in Rechnung, teilweiser Abgleich in Rechnung, teilweiser Abgleich in Gutschrift, teilweiser Abgleich in Erstattungen, teilweiser Abgleich in Belegen, teilweiser Abgleich ausstehender Zahlungen, teilweiser Abgleich ausstehender Gutschriften teilweiser Abgleich ausstehender Belastungen, teilweiser Abgleich von Zahlungen, Rechnung mit Zahlungen abgleichen, Rechnung mit Gutschriften abgleichen, Rechnung mit Kundenzahlung abgleichen, Rechnung mit Kundengutschriften abgleichen, Rechnungen mit Zahlungen abgleichen, Rechnung mit Lieferantenzahlungen abgleichen, Rechnung mit Rückerstattungen abgleichen, Rechnung mit Kreditorengutschriften abgleichen, Rechnungen mit Gutschriften abgleichen Notizen Rechnungen mit Rückerstattungen abgleichen Ausgewählte Zahlungen mit der Zahlungszuordnung von Rechnungen abgleichen.
Japanese
--------
同じウィザード/ポップアップで、複数の請求書、クレジットノート、請求書、返金に対する未払いの支払いを複数の照合します。
         複数の未払いの支払いに対して複数の請求書を調整する
         複数の顧客クレジットノートを使用して複数の未払い借方を調整します。
         複数の仕入先請求書が未払いの借方と調整されます。
         複数の払い戻しは、関連する未払いクレジットと調整されます。
         請求書支払いの調整 請求書支払いの調整 請求書の調整プロセス
         複数の請求書の照合 照合 複数の請求書照合 照合 複数のクレジットノートの照合 照合 複数の返金の照合 照合 複数の領収書の照合 照合
         顧客の支払いを調整する ベンダーの支払いを調整する 顧客のクレジットノートを調整する ベンダーのクレジットノートを調整する 調整する
         未払いのクレジットを請求書に照合する 請求書を未払いのクレジットに照合する 未払いの借方をクレジットノートに照合する 顧客のクレジットノートを照合する クレジットノートを請求書に照合する 未払いの借方を照合する 未払いの請求書を照合する 支払いを照合する 請求書の未払いを照合、クレジットノートの未払いを照合する 請求書の未払いを照合する 払い戻しの未払いの支払いを調整します 仕入先クレジットノートの前払いの未払いを調整します 前払いの調整 顧客の前払いの調整 前払いの仕入先の支払いを調整します
         請求書の一括照合 請求書の一括照合 貸方票の一括照合 返金の一括照合 入金の一括照合 請求書の一括照合 請求書の一括照合 貸方票の一括照合 返金の一括照合 入金の一括照合
         請求書の部分的な調整 請求書の部分的な調整 貸方票の部分的な調整 返金の部分的な調整 領収書の部分的な調整 請求書の部分的な調整 請求書の部分的な調整 貸方票の部分的な調整 返金の部分的な調整 領収書の部分的な調整 未払いのクレジット 支払いの部分的な調整 未払いのクレジット 部分的な照合 未払いの借方 部分的な照合 支払い 請求書と支払の照合 請求書とクレジットノートの照合 請求書と顧客の支払いの照合 請求書と顧客のクレジットノートの照合 請求書と支払の照合 請求書と仕入先の支払の照合 請求書と返金の照合 請求書と仕入先のクレジットノートの照合 請求書とクレジットの照合 メモは請求書と返金を調整します。 選択した支払いと請求書の支払い割り当てを調整します。
Russian
-------
несколько сверок неоплаченных платежей с несколькими счетами-фактурами, кредит-нотами, счетами и возмещениями в одном мастере/всплывающем окне.
         скорректировать несколько счетов-фактур с несколькими неоплаченными платежами
         скорректировать несколько непогашенных дебетов с помощью нескольких кредит-нот клиента.
         Несколько счетов поставщиков сверяются с непогашенным дебетованием.
         Множественные возвраты согласовываются с соответствующими непогашенными кредитами.
         Согласование платежей по счетам Согласование платежей по счетам Процесс сверки в счетах-фактурах
         Множественная сверка счетов-фактур Сверка Множественная сверка счетов Сверка Множественная сверка кредит-нот Сверка Множественная сверка возвратов Сверка Множественная сверка квитанций Сверка
         Выверка платежей клиента Выверка платежей поставщика Выверка кредит-ноты клиента Выверка кредит-ноты поставщика Выверка
         Сверка непогашенных кредитов со счетами-фактурами Сверка счетов-фактур с непогашенными кредитами Сверка непогашенных дебетов с кредит-нотами Сверка кредит-нот клиента Сверка кредит-нот со счетами Сверка непогашенных дебетов Сверка непогашенных счетов Сверка платежей Сверка непогашенных платежей в счетах-фактурах, сверка непогашенных платежей в кредит-нотах Сверка непогашенных платежей по счетам Выверка непогашенного платежа в рамках ВОЗВРАТА Выверка непогашенного платежа по авансовому платежу по кредит-ноте поставщика Выверка авансового платежа Выверка авансового платежа клиента Выверка авансового платежа поставщика
         массовая выверка в счетах-фактурах массовая выверка в счетах массовая выверка в кредит-нотах массовая выверка в возмещениях массовая выверка в квитанциях массовая выверка в счетах-фактурах массовая выверка в счетах массовая выверка в кредит-нотах массовая выверка в возмещениях массовая выверка в квитанциях
         Частичная выверка в счете Частичная выверка в счете Частичная выверка в кредит-ноте Частичная выверка в возмещениях Частичная выверка в поступлениях Частичная выверка в счете Частичная выверка в счете Частичная выверка в кредит-ноте Частичная выверка в возмещениях Частичная выверка в поступлениях Частичная выверка непогашенных платежей Частичная выверка непогашенных кредитов Частичная сверка непогашенных дебетов Частичная сверка платежей Сверка счета с платежами Сверка счета с кредит-нотами Сверка счета с платежом клиента Сверка счета с кредит-нотами клиента Сверка счетов с платежами Сверка счета с платежами поставщика Сверка счета с возмещением Сверка счета с кредит-нотами поставщика Сверка счетов с кредитом примечания сверить счета с возмещениями Согласовать выбранные платежи с распределением платежей по счетам.
Arabic
تسوية المدفوعات المستحقة المتعددة باستخدام العديد من الفواتير وإشعارات الائتمان والفواتير والمبالغ المستردة في نفس المعالج/النوافذ المنبثقة.
         ضبط فواتير متعددة مقابل دفعات مستحقة متعددة
         قم بضبط الديون المستحقة المتعددة مقابل إشعارات ائتمانية متعددة للعملاء.
         تتم تسوية فواتير البائعين المتعددة مع الديون المستحقة.
         تتم تسوية المبالغ المستردة المتعددة مع الاعتمادات المستحقة ذات الصلة.
         تسوية مدفوعات الفاتورة تسوية مدفوعات الفاتورة عملية تسوية مدفوعات الفاتورة في الفواتير
         تسوية متعددة للفواتير تسوية تسوية متعددة للفواتير تسوية تسوية متعددة للمذكرات الدائنة تسوية متعددة للمبالغ المستردة تسوية تسوية متعددة للإيصالات تسوية
         التوفيق بين مدفوعات العملاء التوفيق بين مدفوعات البائع التوفيق بين مذكرة الائتمان الخاصة بالعميل التوفيق بين مذكرة الائتمان الخاصة بالمورد التوفيق
         تسوية الأرصدة المستحقة مع الفواتير تسوية الفواتير مع الاعتمادات المستحقة تسوية الديون المستحقة مع الإشعارات الدائنة تسوية الإشعارات الائتمانية للعميل تسوية الإشعارات الدائنة مع الفواتير تسوية الديون المستحقة تسوية الفواتير المستحقة تسوية المدفوعات تسوية الدفع المستحق في الفواتير، تسوية الدفع المستحق في المذكرات الائتمانية تسوية الدفع المستحق في الفواتير تسوية الدفعة المستحقة في المبالغ المستردة تسوية الدفعة المستحقة في الدفعة المقدمة لمذكرة الائتمان الخاصة بالمورد تسوية الدفعة المقدمة تسوية الدفعة المقدمة للعميل تسوية الدفعة المقدمة للمورد
         تسوية جماعية في الفاتورة تسوية جماعية في الفواتير تسوية جماعية في سندات الدائنة تسوية جماعية في المبالغ المستردة تسوية جماعية في المقبوضات تسوية جماعية في الفاتورة تسوية جماعية في الفواتير تسوية جماعية في سندات الدائنة تسوية جماعية في المبالغ المستردة تسوية جماعية في المقبوضات
         تسوية جزئية في الفاتورة تسوية جزئية في الفاتورة تسوية جزئية في مذكرة الدائن تسوية جزئية في المبالغ المستردة تسوية جزئية في المقبوضات تسوية جزئية في الفاتورة جزئية تسوية في الفاتورة جزئية تسوية في الكمبيالة جزئية تسوية في المبالغ المستردة جزئية تسوية في المقبوضات تسوية جزئية المدفوعات تسوية جزئية الاعتمادات المستحقة التسوية الجزئية للديون المعلقة مدفوعات التسوية الجزئية تسوية الفاتورة مع المدفوعات تسوية الفاتورة مع المذكرات الائتمانية تسوية الفاتورة مع مدفوعات العميل تسوية الفاتورة مع مذكرات الائتمان الخاصة بالعميل تسوية الفواتير مع المدفوعات تسوية الفاتورة مع مدفوعات البائع تسوية الفاتورة مع المبالغ المستردة تسوية الفاتورة مع مذكرات الائتمان الخاصة بالمورد تسوية الفواتير مع الائتمان تسوية الملاحظات بين الفواتير والمبالغ المستردة تسوية المدفوعات المحددة مع تخصيص دفع الفواتير.
	''',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
