from odoo import models, fields, api, _


class AutomationConfigurationStep(models.Model):
    _inherit = 'automation.configuration.step'

    def _trigger_types(self):
        trigger_types = super(AutomationConfigurationStep, self)._trigger_types()

        trigger_types.update({
            "linkedin_mail_open": {
                "name": _("LinkedIn Mail opened"),
                "allow_expiry": True,
                "step_type": ["mail"],
                "color": "text-success",
                "icon": "fa fa-linkedin",
                "message_configuration": _("Opened after"),
                "message": _("Not opened yet"),
            },
        })
        return trigger_types
