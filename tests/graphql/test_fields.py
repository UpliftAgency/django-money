import json

from graphene_django.utils.testing import GraphQLTestCase

from djmoney.money import Money
from tests.testapp.graphql import schema
from tests.testapp.models import ModelWithVanillaMoneyField


MONEY_FIELD_FRAGMENT = """
fragment moneyFieldInfo on MoneyField {
    asString
    amount
    amountStr  # string for accuracy?!
    currency {
        code
        name
        numeric
        symbol
        prefix
        suffix
    }
    amountInt
    amountWith1Digit: formatAmount(decimals: 1)
}
"""


class FieldsTestCase(GraphQLTestCase):
    GRAPHQL_SCHEMA = schema

    def test_query_and_mutation(self):
        ModelWithVanillaMoneyField.objects.create(
            money=Money("100.0", "USD"), second_money=Money("123.321", "EUR")
        )
        response = self.query(
            """
            query {
                allVanilla {
                    id
                    money {
                        ...moneyFieldInfo
                    }
                    secondMoney {
                        ...moneyFieldInfo
                    }
                }
            }

            %s
            """
            % MONEY_FIELD_FRAGMENT
        )

        # This validates the status code and if you get errors
        self.assertResponseNoErrors(response)

        content = json.loads(response.content)
        obj = content["data"]["allVanilla"][0]
        assert obj == {
            "id": "1",
            "money": {
                "asString": "100.00 USD",
                "amount": 100.0,
                "amountInt": 100,
                "amountWith1Digit": "100.0",
                "amountStr": "100.00",
                "currency": {
                    "code": "USD",
                    "name": "US Dollar",
                    "numeric": "840",
                    "symbol": "$",
                    "prefix": "$",
                    "suffix": "",
                },
            },
            "secondMoney": {
                "asString": "123.32 EUR",
                "amount": 123.32,
                "amountInt": 123,
                "amountStr": "123.32",
                "amountWith1Digit": "123.3",
                "currency": {
                    "code": "EUR",
                    "name": "Euro",
                    "numeric": "978",
                    "symbol": "€",
                    "prefix": "",
                    "suffix": "€",
                },
            },
        }

        response_mutate = self.query(
            """
            mutation($id:ID!, $moneyInput:MoneyFieldInput!) {
                updateVanilla(id:$id, money:$moneyInput) {
                    obj {
                        money {
                            ...moneyFieldInfo
                        }
                    }
                    success
                }
            }
            %s
            """
            % MONEY_FIELD_FRAGMENT,
            variables={
                "id": obj["id"],
                "moneyInput": {"amount": "456.78", "currency": "GBP"},
            },
        )
        # This validates the status code and if you get errors
        self.assertResponseNoErrors(response_mutate)

        content = json.loads(response_mutate.content)
        obj_updated = content["data"]["updateVanilla"]["obj"]
        assert obj_updated["money"] == {
            "asString": "456.78 GBP",
            "amount": 456.78,
            "amountInt": 456,
            "amountWith1Digit": "456.8",
            "amountStr": "456.78",
            "currency": {
                "code": "GBP",
                "name": "Pound Sterling",
                "numeric": "826",
                "symbol": "GB£",
                "prefix": "GB£",
                "suffix": "",
            },
        }
