from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)


class Kommun(models.Model):
    _name = 'res.kommun'
    _description = "Sweden Municipality"

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")

