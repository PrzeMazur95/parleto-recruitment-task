import csv

from django.db import transaction
from django.db.models import Sum
from django.core.exceptions import ValidationError
from statements.models import Account, Statement, StatementItem

def statement_import(file_handler):
    idx = 0
    # TODO: TASK → in case of errors database must not change
    # Added transaction.atomic() to ensure that if any error occurs during the import process, all changes made to the database are rolled back.
    # TODO: TASK → optimize database queries during import
    #I would use here Redis, below dicts are only for simplicity purposes. Main goal is that we have to reduce db queries.
    #Simple logic for caching, if account is not in cache, we create it and add to cache, same with statements
    #We had a bug here, because titles for StatementItem were not adding to DB, I fixed it
    #I added statementItem bulk_create to reduce the number of create queries to the database
    with transaction.atomic():
        accounts_cache = {}
        statements_cache = {}
        statement_items = []
        for row in csv.DictReader(file_handler):
            account_key = (row['account'], row['currency'])
            if account_key not in accounts_cache:
                account = Account.objects.get_or_create(
                    name=row['account'],
                    defaults={'currency': row['currency']}
                )[0]
                if account.currency != row['currency']:
                    raise ValidationError('Invalid currency currency ')
                accounts_cache[account_key] = account
            else:
                account = accounts_cache[account_key]
            statement_key = (account.id, row['date'])
            if statement_key not in statements_cache:
                statement = Statement.objects.get_or_create(
                    account=account,
                    date=row['date']
                )[0]
                statements_cache[statement_key] = statement
            else:
                statement = statements_cache[statement_key]
            statement_items.append(StatementItem(
                statement=statement,
                amount=row['amount'],
                currency=row['currency'],
                title=row['title'],
                account=account
            ))
            idx += 1
        StatementItem.objects.bulk_create(statement_items)

        account_balances = StatementItem.objects.values('account').annotate(balance_sum=Sum('amount'))
        for balance_data in account_balances:
            Account.objects.filter(id=balance_data['account']).update(balance=balance_data['balance_sum'])

    return idx

