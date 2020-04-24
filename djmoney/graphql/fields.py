from django.utils.functional import cached_property

import graphene
from graphene.types import InputObjectType, ObjectType, Scalar
from graphql.language import ast

from djmoney.money import Money, get_current_locale

from ..settings import BASE_CURRENCY, DECIMAL_PLACES


class StringMoneyField(Scalar):
    @staticmethod
    def serialize(money):
        if money is None or money == 0:
            money = Money(amount=0, currency=BASE_CURRENCY)

        if isinstance(money, Money):
            return "{0:.{1}f} {2}".format(money.amount, DECIMAL_PLACES, money.currency)

        raise NotImplementedError

    @staticmethod
    def parse_literal(node):
        if isinstance(node, ast.StringValue):
            return StringMoneyField.parse_value(node.value)

    @staticmethod
    def parse_value(value):
        if isinstance(value, Money):
            return value

        amount, currency = value.split(" ")
        return Money(amount=float(amount), currency=currency)


class CurrencyField(ObjectType):
    code = graphene.String(
        description="A ISO-421 3-letter currency. See https://en.wikipedia.org/wiki/ISO_4217#Active_codes",
        required=True,
    )
    name = graphene.String(
        description="A human readable name, e.g. US Dollar", required=True
    )
    numeric = graphene.String(
        description="A ISO-421 numeric code. See https://en.wikipedia.org/wiki/ISO_4217#Active_codes",
        required=True,
    )
    symbol = graphene.String(
        description="The currency's symbol, e.g. $ for USD", required=True
    )
    prefix = graphene.String(
        description="The currency's prefix, e.g. $ for USD", required=True
    )
    suffix = graphene.String(
        description="The currency's symbol, e.g. € for EUR", required=True
    )

    @cached_property
    def _sign_definition(self):
        from moneyed.localization import CurrencyFormatter

        cf = CurrencyFormatter()
        try:
            return cf.get_sign_definition(self.code, get_current_locale())
        except IndexError:
            return ("", "")

    def resolve_symbol(self, info, **kwargs):
        return "".join(self._sign_definition).strip()

    def resolve_prefix(self, info, **kwargs):
        return self._sign_definition[0].strip()

    def resolve_suffix(self, info, **kwargs):
        return self._sign_definition[1].strip()


class MoneyField(ObjectType):
    as_string = StringMoneyField(required=True)

    def resolve_as_string(self, info, **kwargs):
        return self

    amount = graphene.Float(description="The numerical amount.", required=True)
    amount_str = graphene.String(
        description="The string version of the numerical amount.",
        required=True,
    )

    def resolve_amount_str(self, info, **kwargs):
        return self.amount

    currency = graphene.Field(CurrencyField, required=True)

    def resolve_currency(self, info, **kwargs):
        return CurrencyField(
            code=self.currency.code,
            name=self.currency.name,
            numeric=self.currency.numeric,
        )

    format_amount = graphene.Field(graphene.String, decimals=graphene.Int(), required=True)

    def resolve_format_amount(self, info, *, decimals: int, **kwargs):
        return "{0:.{1}f}".format(self.amount, decimals)


class MoneyFieldInput(InputObjectType):
    amount = graphene.String(description="The numerical amount.", required=True)
    currency = graphene.String(description="The ISO-421 3-letter currency code.", required=True)

    def __str__(self):
        return "{0} {1}".format(self.amount, self.currency)

    @property
    def money(self):
        return Money(self.amount, self.currency)


__all__ = ("MoneyField", "MoneyFieldInput", "StringMoneyField")
