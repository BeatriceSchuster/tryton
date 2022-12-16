#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields
from trytond.wizard import Wizard, StateTransition
from trytond.pyson import Eval
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.const import OPERATORS

__all__ = ['Period', 'ClosePeriod', 'ReOpenPeriod']

_STATES = {
    'readonly': Eval('state') == 'close',
}
_DEPENDS = ['state']


class Period(ModelSQL, ModelView):
    'Period'
    __name__ = 'account.period'
    name = fields.Char('Name', required=True)
    code = fields.Char('Code')
    start_date = fields.Date('Starting Date', required=True, states=_STATES,
        depends=_DEPENDS, select=True)
    end_date = fields.Date('Ending Date', required=True, states=_STATES,
        depends=_DEPENDS, select=True)
    fiscalyear = fields.Many2One('account.fiscalyear', 'Fiscal Year',
        required=True, states=_STATES, depends=_DEPENDS, select=True)
    state = fields.Selection([
        ('open', 'Open'),
        ('close', 'Close'),
        ], 'State', readonly=True, required=True)
    post_move_sequence = fields.Many2One('ir.sequence', 'Post Move Sequence',
        required=True, domain=[('code', '=', 'account.move')],
        context={'code': 'account.move'}, states={
            'required': False,
            })
    type = fields.Selection([
            ('standard', 'Standard'),
            ('adjustment', 'Adjustment'),
            ], 'Type', required=True,
        states=_STATES, depends=_DEPENDS, select=True)
    company = fields.Function(fields.Many2One('company.company', 'Company',),
        'get_company', searcher='search_company')

    @classmethod
    def __setup__(cls):
        super(Period, cls).__setup__()
        cls._constraints += [
            ('check_dates', 'periods_overlaps'),
            ('check_fiscalyear_dates', 'fiscalyear_dates'),
            ('check_post_move_sequence', 'check_move_sequence'),
        ]
        cls._order.insert(0, ('start_date', 'ASC'))
        cls._error_messages.update({
            'no_period_date': 'No period defined for this date!',
            'modify_del_period_moves': 'You can not modify/delete ' \
                    'a period with moves!',
            'create_period_closed_fiscalyear': 'You can not create ' \
                    'a period on a closed fiscal year!',
            'open_period_closed_fiscalyear': 'You can not open ' \
                    'a period from a closed fiscal year!',
            'change_post_move_sequence': 'You can not change ' \
                    'the post move sequence ' \
                    'if there is already posted moves in the period',
            'close_period_non_posted_move': 'You can not close ' \
                    'a period with non posted moves!',
            'periods_overlaps': 'You can not have two overlapping periods!',
            'check_move_sequence': 'You must have different ' \
                    'post move sequences per fiscal year ' \
                    'and in the same company!',
            'fiscalyear_dates': 'The period dates must be in ' \
                    'the fiscal year dates',
            })

    @staticmethod
    def default_state():
        return 'open'

    @staticmethod
    def default_type():
        return 'standard'

    def get_company(self, name):
        return self.fiscalyear.company.id

    @classmethod
    def search_company(cls, name, clause):
        return [('fiscalyear.%s' % name,) + tuple(clause[1:])]

    def check_dates(self):
        cursor = Transaction().cursor
        if self.type != 'standard':
            return True
        cursor.execute('SELECT id ' \
                'FROM "' + self._table + '" ' \
                'WHERE ((start_date <= %s AND end_date >= %s) ' \
                        'OR (start_date <= %s AND end_date >= %s) ' \
                        'OR (start_date >= %s AND end_date <= %s)) ' \
                    'AND fiscalyear = %s ' \
                    'AND type = \'standard\' ' \
                    'AND id != %s',
                (self.start_date, self.start_date,
                    self.end_date, self.end_date,
                    self.start_date, self.end_date,
                    self.fiscalyear.id, self.id))
        return not cursor.fetchone()

    def check_fiscalyear_dates(self):
        return not (self.start_date < self.fiscalyear.start_date
            or self.end_date > self.fiscalyear.end_date)

    def check_post_move_sequence(self):
        if self.search([
                    ('post_move_sequence', '=', self.post_move_sequence.id),
                    ('fiscalyear', '!=', self.fiscalyear.id),
                    ]):
            return False
        if (self.post_move_sequence.company
                and (self.post_move_sequence.company.id !=
                    self.fiscalyear.company.id)):
            return False
        return True

    @classmethod
    def find(cls, company_id, date=None, exception=True, test_state=True):
        '''
        Return the period for the company_id
            at the date or the current date.
        If exception is set the function will raise an exception
            if no period is found.
        If test_state is true, it will search on non-closed periods
        '''
        Date = Pool().get('ir.date')

        if not date:
            date = Date.today()
        clause = [
            ('start_date', '<=', date),
            ('end_date', '>=', date),
            ('fiscalyear.company', '=', company_id),
            ('type', '=', 'standard'),
            ]
        if test_state:
            clause.append(('state', '!=', 'close'))
        periods = cls.search(clause, order=[('start_date', 'DESC')], limit=1)
        if not periods:
            if exception:
                cls.raise_user_error('no_period_date')
            else:
                return None
        return periods[0].id

    @classmethod
    def _check(cls, periods):
        Move = Pool().get('account.move')
        moves = Move.search([
                ('period', 'in', [p.id for p in periods]),
                ], limit=1)
        if moves:
            cls.raise_user_error('modify_del_period_moves')

    @classmethod
    def search(cls, args, offset=0, limit=None, order=None, count=False,
            query_string=False):
        args = args[:]

        def process_args(args):
            i = 0
            while i < len(args):
                # add test for xmlrpc and pyson that doesn't handle tuple
                if (isinstance(args[i], tuple) \
                        or (isinstance(args[i], list) and len(args[i]) > 2 \
                        and args[i][1] in OPERATORS)) \
                        and args[i][0] in ('start_date', 'end_date') \
                        and isinstance(args[i][2], (list, tuple)):
                    if not args[i][2][0]:
                        args[i] = ('id', '!=', '0')
                    else:
                        period = cls(args[i][2][0])
                        args[i] = (args[i][0], args[i][1],
                            getattr(period, args[i][2][1]))
                elif isinstance(args[i], list):
                    process_args(args[i])
                i += 1
        process_args(args)
        return super(Period, cls).search(args, offset=offset, limit=limit,
            order=order, count=count, query_string=query_string)

    @classmethod
    def create(cls, vals):
        FiscalYear = Pool().get('account.fiscalyear')
        vals = vals.copy()
        if vals.get('fiscalyear'):
            fiscalyear = FiscalYear(vals['fiscalyear'])
            if fiscalyear.state == 'close':
                cls.raise_user_error('create_period_closed_fiscalyear')
            if not vals.get('post_move_sequence'):
                vals['post_move_sequence'] = fiscalyear.post_move_sequence.id
        return super(Period, cls).create(vals)

    @classmethod
    def write(cls, periods, vals):
        Move = Pool().get('account.move')
        for key in vals.keys():
            if key in ('start_date', 'end_date', 'fiscalyear'):
                cls._check(periods)
                break
        if vals.get('state') == 'open':
            for period in periods:
                if period.fiscalyear.state == 'close':
                    cls.raise_user_error('open_period_closed_fiscalyear')
        if vals.get('post_move_sequence'):
            for period in periods:
                if period.post_move_sequence and \
                        period.post_move_sequence.id != \
                        vals['post_move_sequence']:
                    if Move.search([
                                ('period', '=', period.id),
                                ('state', '=', 'posted'),
                                ]):
                        cls.raise_user_error('change_post_move_sequence')
        super(Period, cls).write(periods, vals)

    @classmethod
    def delete(cls, periods):
        cls._check(periods)
        super(Period, cls).delete(periods)

    @classmethod
    def close(cls, periods):
        pool = Pool()
        JournalPeriod = pool.get('account.journal.period')
        Move = pool.get('account.move')

        if Move.search([
                    ('period', 'in', [p.id for p in periods]),
                    ('state', '!=', 'posted'),
                    ]):
            cls.raise_user_error('close_period_non_posted_move')
        #First close the period to be sure
        #it will not have new journal.period created between.
        cls.write(periods, {
                'state': 'close',
                })
        journal_periods = JournalPeriod.search([
            ('period', 'in', [p.id for p in periods]),
            ])
        JournalPeriod.close(journal_periods)

    @classmethod
    def open_(cls, periods):
        "Open Journal"
        cls.write(periods, {
                'state': 'open',
                })


class ClosePeriod(Wizard):
    'Close Period'
    __name__ = 'account.period.close'
    start_state = 'close'
    close = StateTransition()

    def transition_close(self):
        Period = Pool().get('account.period')
        Period.close(Period.browse(Transaction().context['active_ids']))
        return 'end'


class ReOpenPeriod(Wizard):
    'Re-Open Period'
    __name__ = 'account.period.reopen'
    start_state = 'reopen'
    reopen = StateTransition()

    def transition_reopen(self):
        Period = Pool().get('account.period')
        Period.open_(Period.browse(Transaction().context['active_ids']))
        return 'end'
