from typing import ClassVar, Dict, Final, List, Mapping, Optional, Set, Tuple, Type

from django.core.checks import CheckMessage, Error
from django.db import models


class ExtendableModel(models.Model):
    @classmethod
    def get_children(cls):
        return [subcls for subcls in cls.__subclasses__() if not subcls._meta.abstract]

    class Meta:
        abstract = True


def check_model_extensions(**kwargs):
    return [
        error_message
        for extension in ModelExtension.REGISTRY
        for error_message in extension.check_messages
    ]


class ModelExtension:
    REGISTRY: ClassVar[List['ModelExtension']] = list()
    EXTENDED_FIELDNAMES: ClassVar[Dict[Type[ExtendableModel], Set[str]]] = dict()

    title: Final[str]
    identifier: Final[str]
    prefix: Final[str]
    extended_models: List[Type[ExtendableModel]]
    check_messages: List[CheckMessage]

    @classmethod
    def find_from_identifier(cls, identifier: str):
        return [o for o in cls.REGISTRY if o.identifier == identifier]

    def __init__(self, title: str, identifier: str, prefix: str):
        self.title = title
        self.identifier = identifier
        self.prefix = prefix
        self.extended_models = []
        self.check_messages = []

    def get_namespace_pair(self, key: str) -> Tuple[str, str]:
        if self.prefix:
            return (self.prefix, key.split(':')[1])
        return ('', key)

    def get_prefixed_key(self, key: str) -> str:
        if self.prefix:
            return f'{self.prefix}:{key}'
        return key

    def extend_model(
        self,
        model: Type[ExtendableModel],
        fields: Mapping[str, models.Field],
        opts: Optional[dict] = None,
    ) -> None:
        opts = opts or {}
        if self.check_extend_params(model, fields, opts):
            return
        opts.setdefault('constraints', [])
        opts['constraints'] += self.create_base_constraints(model, fields, opts)
        meta = type('Meta', tuple(), opts or {})
        parent_field = self.create_parent_field(model, fields, opts)
        extended_model = type(
            f'{self.prefix}{model.__name__}',
            (models.Model,),
            {
                'Meta': meta,
                '__module__': self.__module__,
                'ptr': parent_field,
                **fields,
            },
        )
        self.extended_models.append(extended_model)
        self.EXTENDED_FIELDNAMES.setdefault(model, set())
        self.EXTENDED_FIELDNAMES[model] |= set(self.get_prefixed_key(key) for key in fields.keys())

    def create_parent_field(
        self,
        model: Type[ExtendableModel],
        fields: Mapping[str, models.Field],
        opts: dict,
    ) -> models.OneToOneField[ExtendableModel, ExtendableModel]:
        return models.OneToOneField[ExtendableModel, ExtendableModel](
            model,
            on_delete=models.CASCADE,
            related_name=self.prefix,
            db_column='id',
            primary_key=True,
        )

    def create_base_constraints(
        self,
        model: Type[ExtendableModel],
        fields: Mapping[str, models.Field],
        opts: dict,
    ) -> List[models.constraints.BaseConstraint]:
        q = models.Q()
        for field_name in fields.keys():
            if not isinstance(fields[field_name], models.ManyToManyField):
                q |= models.Q(**{f'{field_name}__isnull': False})
        return (
            [models.CheckConstraint(check=q, name=('%(class)s_at_least_one_non_null'))] if q else []
        )

    def check_extend_params(
        self,
        model: Type[ExtendableModel],
        fields: Mapping[str, models.Field],
        opts: dict,
    ) -> List[CheckMessage]:
        errors = [
            *self._check_model_is_extendable(model),
            *self._check_fieldname_clashes(model, fields),
            *self._check_fieldname_reserved(model, fields),
            *self._check_safe_opts(opts),
        ]
        self.check_messages += errors
        return errors

    def _check_model_is_extendable(
        self,
        model: Type[ExtendableModel],
    ) -> List[CheckMessage]:
        if not issubclass(model, ExtendableModel):
            return [
                Error(
                    f'`{model._meta.model_name}` is not an `ExtendableModel`',
                    hint='Only subclasses of `ExtendableModel` may be extended.',
                    obj=model,
                    id='stac.E001',
                )
            ]
        return []

    def _check_fieldname_clashes(
        self,
        model: Type[ExtendableModel],
        fields: Mapping[str, models.Field],
    ) -> List[CheckMessage]:
        previous_fieldnames = self.EXTENDED_FIELDNAMES.get(model, set())
        fieldnames = set(self.get_prefixed_key(key) for key in fields.keys())
        duplicate_keys = previous_fieldnames & fieldnames
        return [
            Error(
                f'`{key}` is already used to extend `{model._meta.model_name}`',
                hint='Fieldnames from extensions cannot clash',
                obj=model,
                id='stac.E002',
            )
            for key in duplicate_keys
        ]

    def _check_fieldname_reserved(
        self,
        model: Type[ExtendableModel],
        fields: Mapping[str, models.Field],
    ) -> List[CheckMessage]:
        reserved_fieldnames = set(('id', 'ptr'))
        fieldnames = fields.keys()
        bad_keys = fieldnames & reserved_fieldnames
        return [
            Error(
                f'`{key}` is a reserved fieldname',
                hint='Fieldnames from extensions cannot use `id` or `ptr`.',
                obj=model,
                id='stac.E003',
            )
            for key in bad_keys
        ]

    def _check_safe_opts(self, opts: dict) -> List[CheckMessage]:
        opt_names = opts.keys()
        safe_names = set(
            (
                'indexes',
                'unique_together',
                'index_together',
                'constraints',
                'db_table',
                'db_tablespace',
                'permissions',
            )
        )
        bad_keys = opt_names - safe_names
        return [
            Error(
                f'`{key}` is not allowed for extended model options',
                hint='Remove this option',
                obj=self,
                id='stac.E004',
            )
            for key in bad_keys
        ]
