import graphene
from graphene_django.types import DjangoObjectType

from djmoney.graphql.fields import MoneyField, MoneyFieldInput
from djmoney.money import Money

from .models import ModelWithVanillaMoneyField


class VanillaType(DjangoObjectType):
    class Meta:
        model = ModelWithVanillaMoneyField
        fields = ("id",)

    money = graphene.Field(MoneyField)
    second_money = graphene.Field(MoneyField)


class TestappQuery(object):
    all_vanilla = graphene.List(VanillaType)

    def resolve_all_vanilla(self, info, **kwargs):
        return ModelWithVanillaMoneyField.objects.all()


class Query(TestappQuery, graphene.ObjectType):
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project
    pass


class UpdateVanilla(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        money = MoneyFieldInput(required=True)

    success = graphene.Boolean(required=True)
    obj = graphene.Field(VanillaType)

    def mutate(root, info, id, money):
        ModelWithVanillaMoneyField.objects.filter(id=id).update(
            money=Money(money.amount, money.currency),
        )
        obj = ModelWithVanillaMoneyField.objects.get(id=id)
        return UpdateVanilla(obj=obj, success=True)


class Mutations(graphene.ObjectType):
    update_vanilla = UpdateVanilla.Field()


schema = graphene.Schema(query=Query, mutation=Mutations)
