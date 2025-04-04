from django.db import models


def report_turnover_by_year_month(period_begin, period_end):
    # TODO: TASK → make report using 1 database query without any math in python
    # example output
    return {
        "2009-11": {
            {
                "incomes": {
                    "PLN": 120
                },
                "expenses": {
                    "PLN": 100
                }
            }
        }
    }


class Account(models.Model):
    name = models.CharField(max_length=100)
    currency = models.CharField(max_length=3)
    # TODO: TASK → add field balance that will update automatically
    # I was thinking about two approaches:
    #   - we can use signals or extend statementItem save method, but each time balance will be updated when new item is added
    #   - or we can do once balance update after import.
    # I have chosen the second approach, because we are keeping eye on performance.
    # In my opinion, we should use signal or extend save method only when we need to update this field in real time,
    # but in this case of multiple rows imports, for better performance I used single update after import
    # so it depends on business logic.
    # Large imports should be done in batch, small individual updates, like in app by user, can be done with signals or extended save method.
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        indexes = [
            models.Index(fields=['name', 'currency']),
        ]
     
    def __str__(self):
        return f'{self.name}[{self.currency}]'


class Statement(models.Model):
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    date = models.DateField()
    # TODO: TASK → make sure that account and date is unique on database level
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['account', 'date'], name='unique_account_date_pair')
        ]

    def __str__(self):
        return f'{self.account} → {self.date}'
    

class StatementItem(models.Model):
    statement = models.ForeignKey(Statement, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    currency = models.CharField(max_length=3)
    title = models.CharField(max_length=100)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    # TODO:  TASK → add field comments (type text)

    class Meta:
        indexes = [
            models.Index(fields=['account', 'currency']),
        ]
    

    def __str__(self):
        return f'[{self.statement}] {self.amount} {self.currency} → {self.title}'
