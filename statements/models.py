from .date_preparator import ValidateFormat, PrepareWholeMonthDate, AddDefaultDayToMonth, ValidateDateOrder, FinalParser
from django.db import models
from django.db.models import Sum, Case, When, Value, F

def prepare_dates(period_begin, period_end):
    try:
        # order of handlers is important, especially the last two. They are also proper ordered in its file with comments.
        # if we will have new example of date format (on backend we should have it prepared in one format given from FE),
        # but in our case we should add new handler to its file and to proper place in the list below.
        handlers = [
            ValidateFormat(),
            PrepareWholeMonthDate(),
            AddDefaultDayToMonth(),
            ValidateDateOrder(),
            FinalParser()
        ]
        for handler in handlers:
            if handler.can_handle(period_begin, period_end):
                period_begin, period_end = handler.prepare(period_begin, period_end)
        return period_begin, period_end

    except ValueError as e:
        raise ValueError(e)

def report_turnover_by_year_month(period_begin, period_end):
    # TODO: TASK → make report using 1 database query without any math in python
    # I was not sure how to behave with internal transfers, but i kept them in incomes and expenses, so overall is 0
    # It is hard now to exclude it, I do not know if the transfer title always be the same, to take it into consideration
    # Second thing is, that I am not pretty sure if models are good place to put this function, better is some service with reports
    # but still do not know how test are written, so I will not refactor it.
    try:
        result_date_range_key = f"{period_begin}-{period_end}" if period_begin != period_end else f"{period_begin}"
        period_begin, period_end = prepare_dates(period_begin, period_end)
    except ValueError as e:
        return f"Error: {e}"

    transactions_amounts = StatementItem.objects.filter(
        statement_id__in=Statement.objects.filter(date__range=[period_begin, period_end]).values_list('id', flat=True)
    ).annotate(
        negative_amount=Sum(
            Case(
                When(amount__lt=0, then=F('amount')),
                default=Value(0),
                output_field=models.DecimalField()
            )
        ),
        positive_amount=Sum(
            Case(
                When(amount__gt=0, then=F('amount')),
                default=Value(0),
                output_field=models.DecimalField()
            )
        )
    ).aggregate(
        total_negative_amount=Sum('negative_amount'),
        total_positive_amount=Sum('positive_amount')
    )

    if not transactions_amounts['total_positive_amount'] and transactions_amounts['total_negative_amount'] is None:
        return f"There are no transactions in the given period: {result_date_range_key}"

    result = {
        result_date_range_key: {
            "incomes": {
                "PLN": float(abs(transactions_amounts['total_positive_amount']))
            },
            "expenses": {
                "PLN": float(abs(transactions_amounts['total_negative_amount']))
            }
        }
    }

    return result

    # example output - this dict has wrong format, and will raise TypeError.
    # dict with incomes and expenses cannot be element of set - "unhashable type: 'dict'"
    # return {
    #     "2009-11": {
    #         {
    #             "incomes": {
    #                 "PLN": 120
    #             },
    #             "expenses": {
    #                 "PLN": 100
    #             }
    #         }
    #     }
    # }


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
    comments = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['account', 'currency']),
        ]
    

    def __str__(self):
        return f'[{self.statement}] {self.amount} {self.currency} → {self.title}'
