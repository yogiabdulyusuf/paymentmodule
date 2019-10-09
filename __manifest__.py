{
	"name": "Payment Module Parkir System",
	"version": "10.0.1.0",
	"depends": [
		"base",
		"mail",
		"report",
		"base_external_dbsource",
	],
	"author": "jakc-labs",
	"category": "PaymentModule",
	'website': 'http://www.jakc-labs.com',
	"description": """

Payment Module
======================================================================

* Payment Module Parkir System

""",
	"data": [
		"security/payment_module_security.xml",
		"security/ir.model.access.csv",
		"view/request_transstiker_view.xml",
		"view/trans_stiker_view.xml",
		"view/detail_transstiker_view.xml",
		"view/billing_view.xml",
		"view/setting_view.xml",
		"view/stasiun_kerja_view.xml",
		"data/ir_sequence.xml",
		"report/report_request_stiker.xml",
		"report/report_request_stiker_template.xml",
		"report/report_requestdetails.xml",
		"report/report_request_details.xml",
		"report/report_monthly_billing.xml",
		"report/report_monthly_billing_template.xml",
		"wizard/wizard_report_request_details_view.xml",
		"wizard/wizard_report_request_transaction_view.xml",
		"wizard/wizard_add_card_member_view.xml",
		"wizard/wizard_not_approve_view.xml",
		"wizard/wizard_report_billing_view.xml",
		"wizard/wizard_check_kartu_view.xml",
		"view/top_menu.xml",
	],
	"installable": True,
	"auto_install": False,
    "application": True,
}