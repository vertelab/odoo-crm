{
    'name':'crm_insurance',
    'description': 'new template for company insurance',
    'version':'1.0',
    'author':'Vertel AB',

    'data': [
        'views/res_partner_views.xml',
        'data/insurance.license.csv',
        'data/insurance.permission.csv',
        'security/ir.model.access.csv'
    ],
    'category': 'crm',
    'depends': ['crm'],
    'application': True,
}

