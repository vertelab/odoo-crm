# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Product(models.Model):
    _inherit = 'product.template'

    membership_product_ids = fields.Many2many(comodel_name='product.template', relation='membership_product_rel', column1='product_id',column2='member_product_id', string='Membership Products' ,domain="[('membership','=',True), ('type', '=', 'service')]")
   

   
