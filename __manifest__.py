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
		"view/payment_module_view.xml",
		"view/billing_view.xml",
		"view/setting_view.xml",
		"data/ir_sequence.xml",		
		"report/report_request_stiker.xml",
		"report/report_request_stiker_template.xml",
		"report/report_requestdetails.xml",
		"report/report_request_details.xml",
		"wizard/wizard_report_request_details_view.xml",
		"view/top_menu.xml",
	],
	"installable": True,
	"auto_install": False,
    "application": True,
}