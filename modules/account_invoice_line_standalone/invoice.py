#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval
import copy


class Invoice(ModelSQL, ModelView):
    _name = 'account.invoice'

    def __init__(self):
        super(Invoice, self).__init__()
        self.lines = copy.copy(self.lines)
        add_remove = [
            ('invoice_type', '=', Eval('type')),
            ('party', '=', Eval('party')),
            ('currency', '=', Eval('currency')),
            ('company', '=', Eval('company')),
            ('invoice', '=', False),
        ]

        if not self.lines.add_remove:
            self.lines.add_remove = add_remove
        else:
            self.lines.add_remove = copy.copy(self.lines.add_remove)
            self.lines.add_remove = [
                add_remove,
                self.lines.add_remove,
            ]
        self._reset_columns()

Invoice()


class InvoiceLine(ModelSQL, ModelView):
    _name = 'account.invoice.line'

    def _view_look_dom_arch(self, cursor, user, tree, type, context=None):
        if context is None:
            context = {}
        if type == 'form' and context.get('standalone'):
            tree_root = tree.getroottree().getroot()
            if tree_root.get('cursor') == 'product':
                tree_root.set('cursor', 'party')
        return super(InvoiceLine, self)._view_look_dom_arch(cursor, user, tree,
                type, context=context)

InvoiceLine()
