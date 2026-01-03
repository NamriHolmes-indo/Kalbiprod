from odoo import models, fields, api
from odoo.exceptions import AccessError


class SimplePricingOrder(models.Model):
    _name = "simple.pricing.order"
    _description = "Simple Pricing Order"

    name = fields.Char(string="Judul Produk", default="New", copy=False)
    title = fields.Char(string="Judul / Nama Produk", default="New", required=True)
    _rec_name = "title"

    date = fields.Datetime(string="Date", default=fields.Datetime.now)
    note = fields.Text(string="Notes")

    line_ids = fields.One2many(
        "simple.pricing.order.line", "order_id", string="Order Lines"
    )

    amount_untaxed = fields.Monetary(
        string="Subtotal", compute="_compute_amount", store=True
    )

    amount_tax = fields.Monetary(string="Tax", compute="_compute_amount", store=True)

    amount_total = fields.Monetary(
        string="Total", compute="_compute_amount", store=True
    )

    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.company.currency_id
    )

    extra_line_ids = fields.One2many(
        "simple.pricing.order.extra", "order_id", string="Variabel Jual Tambahan"
    )

    extra_amount = fields.Monetary(
        string="Total Variabel Tambahan", compute="_compute_amount", store=True
    )

    optimal_margin = fields.Float(
        string="Margin Optimal (%)", compute="_compute_optimal_pricing"
    )

    optimal_price = fields.Monetary(
        string="Harga Jual Optimal",
        compute="_compute_optimal_pricing",
        currency_field="currency_id",
    )

    target_price = fields.Monetary(
        string="Target Harga Jual", currency_field="currency_id"
    )

    target_margin = fields.Float(
        string="Margin dari Target (%)", compute="_compute_target_margin", store=True
    )

    price_no_markup = fields.Monetary(
        string="Saran harga normal",
        compute="_compute_price_suggestions",
        currency_field="currency_id",
    )

    price_half_markup = fields.Monetary(
        string="Saran harga tengah",
        compute="_compute_price_suggestions",
        currency_field="currency_id",
    )

    price_full_markup = fields.Monetary(
        string="Saran harga Optimal",
        compute="_compute_price_suggestions",
        currency_field="currency_id",
    )

    selected_price = fields.Monetary(
        string="Harga Terpilih",
        currency_field="currency_id",
        tracking=True,
    )

    selected_strategy = fields.Selection(
        [
            ("none", "Tanpa Markup"),
            ("half", "Markup 1/2"),
            ("full", "Markup Optimal"),
        ],
        string="Strategi Harga",
        tracking=True,
    )

    market_summary = fields.Text(
        string="Ringkasan Pasar (AI)",
        readonly=True,
    )

    market_price_min = fields.Monetary(
        string="Harga Pasar Minimum",
        currency_field="currency_id",
        readonly=True,
    )

    market_price_max = fields.Monetary(
        string="Harga Pasar Maksimum",
        currency_field="currency_id",
        readonly=True,
    )

    market_positioning = fields.Selection(
        [
            ("low", "Low Market"),
            ("mid", "Mid Market"),
            ("premium", "Premium Market"),
        ],
        string="Positioning Pasar",
        readonly=True,
    )

    market_confidence = fields.Float(
        string="Confidence (%)",
        readonly=True,
    )

    state = fields.Selection(
        [
            ("draft", "Draft (R&D)"),
            ("review", "Menunggu Approval"),
            ("approved", "Approved"),
        ],
        default="draft",
        tracking=True,
    )

    can_edit = fields.Boolean(compute="_compute_can_edit")
    can_select_price = fields.Boolean(compute="_compute_can_select_price")
    can_submit_review = fields.Boolean(compute="_compute_can_submit_review")

    def _compute_can_edit(self):
        for rec in self:
            rec.can_edit = rec.state != "approved"

    def _compute_can_select_price(self):
        for rec in self:
            rec.can_select_price = rec.state != "approved" and rec.env.user.has_group(
                "kalbiprod.group_kalbiprod_manager"
            )

    def _compute_can_submit_review(self):
        for rec in self:
            rec.can_submit_review = rec.state == "draft" and rec.env.user.has_group(
                "kalbiprod.group_kalbiprod_rnd"
            )

    def action_submit_review(self):
        self.write({"state": "review"})

    @api.depends("line_ids.subtotal", "line_ids.tax_amount", "extra_line_ids.amount")
    def _compute_amount(self):
        for order in self:
            base = sum(order.line_ids.mapped("subtotal"))
            tax = sum(order.line_ids.mapped("tax_amount"))
            extra = sum(order.extra_line_ids.mapped("amount"))

            order.amount_untaxed = base
            order.amount_tax = tax
            order.extra_amount = extra
            order.amount_total = base + tax + extra

    @api.model
    def create(self, vals_list):
        orders = super().create(vals_list)

        for order in orders:
            if order.name == "New":
                order.name = (
                    self.env["ir.sequence"].next_by_code("simple.pricing.order")
                    or "S00001"
                )

            if not order.title:
                order.title = order.name

            has_packing = order.extra_line_ids.filtered(lambda x: x.is_default_packing)

            if not has_packing:
                self.env["simple.pricing.order.extra"].create(
                    {
                        "order_id": order.id,
                        "name": "Packing Tambahan",
                        "percent": 5.0,
                        "is_default_packing": True,
                    }
                )

        return orders

    @api.depends("target_price")
    def _compute_target_margin(self):
        for order in self:
            if order.amount_total:
                order.target_margin = (
                    (order.target_price - order.amount_total) / order.amount_total * 100
                )
            else:
                order.target_margin = 0.0

    @api.depends("amount_untaxed", "extra_amount")
    def _compute_optimal_pricing(self):
        for order in self:
            base = order.amount_untaxed or 0.0
            extra = order.extra_amount or 0.0

            markup = 0.0

            if base <= 0:
                markup = 0.0

            elif extra <= 0:
                markup = 50.0

            else:
                ratio = (base / extra) * 100
                if ratio <= 30:
                    markup = 50.0
                elif ratio <= 50:
                    markup = 75.0
                elif ratio <= 100:
                    markup = 100.0
                else:
                    markup = 150.0

            order.optimal_margin = markup
            order.optimal_price = base + (base * markup / 100)

    @api.depends("amount_untaxed", "extra_amount", "optimal_margin")
    def _compute_price_suggestions(self):
        for order in self:
            base_cost = order.amount_untaxed + order.extra_amount
            markup = order.optimal_margin or 0.0

            order.price_no_markup = base_cost
            order.price_half_markup = base_cost * (1 + (markup / 2) / 100)
            order.price_full_markup = base_cost * (1 + markup / 100)

    @api.onchange("title")
    def _onchange_title_sync_name(self):
        if self.title:
            self.name = self.title

    def action_select_price(self):
        if not self.env.user.has_group("kalbiprod.group_kalbiprod_manager"):
            raise AccessError("Hanya Manager yang boleh memilih harga jual.")

        strategy = self.env.context.get("strategy")

        for order in self:
            if strategy == "none":
                order.selected_price = order.price_no_markup
            elif strategy == "half":
                order.selected_price = order.price_half_markup
            elif strategy == "full":
                order.selected_price = order.price_full_markup

            order.selected_strategy = strategy
            order.state = "approved"

            order.message_post(
                body=f"Harga diset oleh Manager ({strategy}) sebesar {order.selected_price}"
            )


class SimplePricingOrderLine(models.Model):
    _name = "simple.pricing.order.line"
    _description = "Simple Pricing Order Line"

    order_id = fields.Many2one("simple.pricing.order", ondelete="cascade")

    product_id = fields.Many2one("product.product", string="Product", required=True)

    qty = fields.Float(string="Quantity", default=1.0)

    uom_id = fields.Many2one("uom.uom", related="product_id.uom_id", readonly=True)

    price_unit = fields.Float(string="Unit Price")

    tax_ids = fields.Many2many("account.tax", string="Tax")

    currency_id = fields.Many2one(
        "res.currency", related="order_id.currency_id", store=True
    )

    subtotal = fields.Monetary(
        string="Total Bahan", compute="_compute_amount", store=True
    )
    tax_amount = fields.Monetary(
        string="Tax Amount", compute="_compute_amount", store=True
    )
    total = fields.Monetary(string="Total", compute="_compute_amount", store=True)

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            self.price_unit = self.product_id.lst_price

    @api.depends("qty", "price_unit", "tax_ids")
    def _compute_amount(self):
        for line in self:
            line.subtotal = line.qty * line.price_unit
            if line.tax_ids:
                taxes = line.tax_ids.compute_all(
                    line.price_unit,
                    currency=line.currency_id,
                    quantity=line.qty,
                    product=line.product_id,
                    partner=False,
                )
                line.tax_amount = taxes["total_included"] - taxes["total_excluded"]
                line.total = taxes["total_included"]
            else:
                line.tax_amount = 0.0
                line.total = line.subtotal


class SimplePricingOrderExtra(models.Model):
    _name = "simple.pricing.order.extra"
    _description = "Pricing Extra Variable"
    _sql_constraints = [
        models.Constraint(
            "UNIQUE(order_id, is_default_packing)", "Default packing hanya boleh satu."
        )
    ]

    order_id = fields.Many2one("simple.pricing.order", ondelete="cascade")

    name = fields.Char(string="Nama Variabel", required=True)

    percent = fields.Float(
        string="Persentase (%)", help="Persentase dari total harga bahan"
    )

    amount = fields.Monetary(string="Nilai", compute="_compute_amount", store=True)

    currency_id = fields.Many2one(
        "res.currency", related="order_id.currency_id", store=True
    )

    is_default_packing = fields.Boolean(
        string="Default Packing",
        default=False,
    )

    @api.depends("percent", "order_id.amount_untaxed")
    def _compute_amount(self):
        for line in self:
            base = line.order_id.amount_untaxed or 0.0
            line.amount = base * (line.percent / 100.0)
