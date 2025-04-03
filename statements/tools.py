import csv

from django.db import transaction
from django.core.exceptions import ValidationError
from statements.models import Account, Statement, StatementItem

def statement_import(file_handler):
    idx = 0
    # TODO: TASK → in case of errors database must not change
    # Added transaction.atomic() to ensure that if any error occurs during the import process, all changes made to the database are rolled back.
    # TODO: TASK → optimize database queries during import
    #I would use here Redis, below dicts are only for simplicity purposes. Main goal is that we have to reduce db queries.
    #Simple logic for caching, if account is not in cache, we create it and add to cache, same with statements
    with transaction.atomic():
        accounts_cache = {}
        statements_cache = {}
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
            StatementItem.objects.create(
                statement=statement,
                amount=row['amount'],
                currency=row['currency'],
            )
            idx += 1
    return idx

