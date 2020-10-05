from django.contrib.auth.models import User
import factory.django

from rgd.core import models


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.SelfAttribute('email')
    email = factory.Faker('safe_email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')


class TaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Task

    name = factory.Faker('sentence', nb_words=2)
    creator = factory.SubFactory(UserFactory)
