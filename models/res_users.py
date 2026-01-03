from odoo import models, api


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def create(self, vals):
        user = super().create(vals)

        if not user.share:
            user.groups_id = [(4, self.env.ref("kalbiprod.group_rnd").id)]

        return user
