# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_EVEN
from operator import itemgetter

from trytond.model import ModelSQL, ModelView, Workflow, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from trytond.transaction import Transaction

__all__ = ['Configuration', 'LandedCost', 'LandedCost_Shipment', 'InvoiceLine']


class Configuration:
    __name__ = 'account.configuration'
    __metaclass__ = PoolMeta
    landed_cost_sequence = fields.Property(fields.Many2One('ir.sequence',
            'Landed Cost Sequence', domain=[
                ('company', 'in',
                    [Eval('context', {}).get('company', -1), None]),
                ('code', '=', 'account.landed_cost'),
                ], required=True))


class LandedCost(Workflow, ModelSQL, ModelView):
    'Landed Cost'
    __name__ = 'account.landed_cost'
    _rec_name = 'code'
    code = fields.Char('Code', select=True, readonly=True)
    company = fields.Many2One('company.company', 'Company', required=True,
        states={
            'readonly': Eval('state') != 'draft',
            },
        depends=['state'])
    shipments = fields.Many2Many('account.landed_cost-stock.shipment.in',
        'landed_cost', 'shipment', 'Shipments',
        states={
            'readonly': Eval('state') != 'draft',
            },
        domain=[
            ('company', '=', Eval('company')),
            ('state', 'in', ['received', 'done']),
            ],
        depends=['company', 'state'])
    invoice_lines = fields.One2Many('account.invoice.line', 'landed_cost',
        'Invoice Lines',
        states={
            'readonly': Eval('state') != 'draft',
            },
        add_remove=[
            ('landed_cost', '=', None),
            ],
        domain=[
            ('invoice.state', 'in', ['posted', 'paid']),
            ('invoice.type', '=', 'in_invoice'),
            ('product.template.landed_cost', '=', True),
            ('type', '=', 'line'),
            ],
        depends=['state'])
    allocation_method = fields.Selection([
            ('value', 'By Value'),
            ], 'Allocation Method', required=True,
        states={
            'readonly': Eval('state') != 'draft',
            },
        depends=['state'])
    posted_date = fields.Date('Posted Date', readonly=True)
    state = fields.Selection([
            ('draft', 'Draft'),
            ('posted', 'Posted'),
            ('cancel', 'Canceled'),
            ], 'State', readonly=True)

    @classmethod
    def __setup__(cls):
        super(LandedCost, cls).__setup__()

        cls._order = [
            ('code', 'DESC'),
            ('id', 'DESC'),
            ]
        cls._transitions |= set((
                ('draft', 'posted'),
                ('draft', 'cancel'),
                ('cancel', 'draft'),
                ))
        cls._buttons.update({
                'cancel': {
                    'invisible': Eval('state') != 'draft',
                    },
                'draft': {
                    'invisible': Eval('state') != 'cancel',
                    },
                'post': {
                    'invisible': Eval('state') != 'draft',
                    },
                })

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_allocation_method():
        return 'value'

    @staticmethod
    def default_state():
        return 'draft'

    @classmethod
    @ModelView.button
    @Workflow.transition('cancel')
    def cancel(cls, landed_costs):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('draft')
    def draft(cls, landed_costs):
        pass

    @property
    def cost(self):
        pool = Pool()
        Currency = pool.get('currency.currency')

        currency = self.company.currency
        cost = Decimal(0)

        for line in self.invoice_lines:
            cost += Currency.compute(line.invoice.currency, line.amount,
                currency, round=False)
        return cost

    def allocate_cost_by_value(self):
        self._allocate_cost(self._get_value_factors())

    def _get_value_factors(self):
        "Return the factor for each move based on value"
        pool = Pool()
        Currency = pool.get('currency.currency')

        currency = self.company.currency
        moves = [m for s in self.shipments for m in s.incoming_moves
            if m.state != 'cancel']

        sum_value = 0
        unit_prices = {}
        for move in moves:
            unit_price = Currency.compute(move.currency, move.unit_price,
                currency, round=False)
            unit_prices[move.id] = unit_price
            sum_value += unit_price * Decimal(str(move.quantity))

        factors = {}
        length = Decimal(len(moves))
        for move in moves:
            quantity = Decimal(str(move.quantity))
            if not sum_value:
                factors[move.id] = 1 / length
            else:
                factors[move.id] = quantity * unit_prices[move.id] / sum_value
        return factors

    def _allocate_cost(self, factors):
        "Allocate cost on moves using factors"
        pool = Pool()
        Move = pool.get('stock.move')
        Currency = pool.get('currency.currency')

        cost = self.cost
        currency = self.company.currency
        moves = [m for s in self.shipments for m in s.incoming_moves
            if m.state != 'cancel']

        costs = []
        digit = Move.unit_price.digits[1]
        exp = Decimal(str(10.0 ** -digit))
        difference = cost
        for move in moves:
            quantity = Decimal(str(move.quantity))
            move_cost = cost * factors[move.id]
            unit_landed_cost = (move_cost / quantity).quantize(exp,
                rounding=ROUND_DOWN)
            costs.append({
                    'unit_landed_cost': unit_landed_cost,
                    'difference': move_cost - (unit_landed_cost * quantity),
                    'move': move,
                    })
            difference -= unit_landed_cost * quantity
        costs.sort(key=itemgetter('difference'), reverse=True)
        for cost in costs:
            move = cost['move']
            quantity = Decimal(str(move.quantity))
            if exp * quantity <= difference:
                cost['unit_landed_cost'] += exp
                difference -= exp * quantity
            if difference < exp:
                break

        for cost in costs:
            move = cost['move']
            unit_landed_cost = Currency.compute(
                currency, cost['unit_landed_cost'],
                move.currency, round=False)
            unit_landed_cost = unit_landed_cost.quantize(
                exp, rounding=ROUND_HALF_EVEN)
            if move.unit_landed_cost is None:
                move.unit_landed_cost = 0
            move.unit_price += unit_landed_cost
            move.unit_landed_cost += unit_landed_cost
        Move.save(moves)

    @classmethod
    @ModelView.button
    @Workflow.transition('posted')
    def post(cls, landed_costs):
        pool = Pool()
        Date = pool.get('ir.date')

        for landed_cost in landed_costs:
            getattr(landed_cost, 'allocate_cost_by_%s' %
                landed_cost.allocation_method)()
        cls.write(landed_costs, {
                'posted_date': Date.today(),
                })

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        Sequence = pool.get('ir.sequence')
        Config = pool.get('account.configuration')

        vlist = [v.copy() for v in vlist]
        config = Config(1)
        for values in vlist:
            values['code'] = Sequence.get_id(config.landed_cost_sequence.id)
        return super(LandedCost, cls).create(vlist)


class LandedCost_Shipment(ModelSQL):
    'Landed Cost - Shipment'
    __name__ = 'account.landed_cost-stock.shipment.in'
    landed_cost = fields.Many2One('account.landed_cost', 'Landed Cost',
        required=True, select=True)
    shipment = fields.Many2One('stock.shipment.in', 'Shipment',
        required=True)


class InvoiceLine:
    __name__ = 'account.invoice.line'
    __metaclass__ = PoolMeta
    landed_cost = fields.Many2One('account.landed_cost', 'Landed Cost',
        readonly=True, select=True,
        states={
            'invisible': ~Eval('landed_cost'),
            })

    @classmethod
    def __setup__(cls):
        super(InvoiceLine, cls).__setup__()
        cls._check_modify_exclude.add('landed_cost')
