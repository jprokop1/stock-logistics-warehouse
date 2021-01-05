# © 2018 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import ValidationError


class StockInventory(models.Model):
    _inherit = "stock.inventory"

    def action_generate_putaway_rules(self):
        self._generate_putaway_rules()

    def _generate_putaway_rules(self):
        for record in self:
            if record.state != "done":
                raise ValidationError(
                    _(
                        "Please validate the inventory before generating "
                        "the putaway strategy."
                    )
                )
            for location in record.location_ids:
                record.line_ids._generate_putaway_rules(location)


class StockInventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    def _generate_putaway_rules(self, inventory_location):
        # Eliminate lines for other IN locations
        # and eliminate lines where quantity is null
        self.filtered(
            lambda x: x.location_id._is_child(inventory_location) and x.product_qty > 0
        )._update_product_putaway_rule(inventory_location)

    def _update_product_putaway_rule(self, location_in):
        putaway_rule_obj = self.env["stock.putaway.rule"]
        putaway_rules = putaway_rule_obj.search(
            [
                ("product_id", "in", self.mapped("product_id").ids),
                ("location_in_id", "=", location_in.id),
            ]
        )
        for record in self:
            putaway_rule = putaway_rules.filtered(
                lambda x: x.product_id == record.product_id
            )
            if putaway_rule:
                putaway_rule.location_out_id = record.location_id
            else:
                putaway_rule_obj.create(
                    {
                        "product_id": record.product_id.id,
                        "location_in_id": location_in.id,
                        "location_out_id": record.location_id.id,
                    }
                )
