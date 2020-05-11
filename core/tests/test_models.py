from django.test import TestCase
import factory

from django.contrib.auth.models import User

from .. import models


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: 'user_%d' % n)
    email = factory.Sequence(lambda n: 'user_%d' % n)


class TaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Task

    name = factory.Faker('sentence', nb_words=2)
    creator = factory.SubFactory(UserFactory)


class TaskModelTest(TestCase):
    def test_get_absolute_url(self):
        task = TaskFactory()
        # This will also fail if the urlconf is not defined.
        assert task.get_absolute_url().startswith('/task/1-')
