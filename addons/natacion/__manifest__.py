# -*- coding: utf-8 -*-
{
    'name': "natacion",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
    Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'report/report_paper_format.xml',
        'report/report_results.xml',  
        'report/report_ticket.xml',
        'views/session_results_wizard.xml',
        'views/ticket_wizard_view.xml',
        'views/swimmer_registration_wizard.xml',
        'views/championships_wizard.xml',
        'views/views.xml',
        'views/swimmers.xml',
        'views/clubs.xml',
        'views/categories.xml',
        'views/styles.xml',
        'views/besttimes.xml',
        'views/championships.xml',
        'views/sessions.xml',
        'views/tests.xml',
        'views/series.xml',
        'views/results.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ]
}