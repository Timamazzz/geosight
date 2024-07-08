from rest_framework.metadata import SimpleMetadata
from collections import OrderedDict
from django.utils.encoding import force_str
from rest_framework import serializers
from rest_framework.utils.field_mapping import ClassLookupDict

from geosight.utils.fields import PhoneField, PasswordField


class OptionsMetadata(SimpleMetadata):
    label_lookup = ClassLookupDict({
        serializers.Field: 'field',
        serializers.BooleanField: 'boolean',
        serializers.CharField: 'string',
        serializers.UUIDField: 'string',
        serializers.URLField: 'url',
        serializers.EmailField: 'email',
        serializers.RegexField: 'regex',
        serializers.SlugField: 'slug',
        serializers.IntegerField: 'integer',
        serializers.FloatField: 'float',
        serializers.DecimalField: 'decimal',
        serializers.DateField: 'date',
        serializers.DateTimeField: 'datetime',
        serializers.TimeField: 'time',
        serializers.ChoiceField: 'choice',
        serializers.MultipleChoiceField: 'multiple choice',
        serializers.FileField: 'file upload',
        serializers.ImageField: 'image upload',
        serializers.ListField: 'list',
        serializers.DictField: 'nested object',
        serializers.Serializer: 'nested object',
        PhoneField: 'phone',
        PasswordField: 'password',
    })

    def determine_metadata(self, request, view):
        metadata = super().determine_metadata(request, view)
        serializer_list = getattr(view, 'serializer_list', {})
        if serializer_list:
            actions_metadata = {}
            for key, serializer_class in serializer_list.items():
                serializer_instance = serializer_class()
                fields = self.get_serializer_info(serializer_instance)
                actions_metadata[key] = fields
            metadata['actions'] = actions_metadata

        return metadata

    def get_serializer_info(self, serializer):
        fields = OrderedDict([
            (field_name, self.get_field_info(field))
            for field_name, field in serializer.fields.items()
            if not isinstance(field, serializers.HiddenField)
        ])

        if hasattr(serializer, 'child'):
            fields = self.get_serializer_info(serializer.child)

        return fields

    def get_field_info(self, field):
        field_info = OrderedDict()
        field_info['type'] = self.label_lookup[field]
        field_info['required'] = getattr(field, 'required', False)

        attrs = [
            'read_only', 'label', 'help_text',
            'min_length', 'max_length',
            'min_value', 'max_value'
        ]

        for attr in attrs:
            value = getattr(field, attr, None)
            if value is not None and value != '':
                field_info[attr] = force_str(value, strings_only=True)

        self.set_styles_field(field_info, field)

        if getattr(field, 'child', None):
            field_info['child'] = self.get_field_info(field.child)
        elif getattr(field, 'fields', None):
            field_info['children'] = self.get_serializer_info(field)

        if (not field_info.get('read_only')) and \
                (isinstance(field, (
                        serializers.RelatedField, serializers.ManyRelatedField, serializers.PrimaryKeyRelatedField)) or
                 hasattr(field, 'choices')):
            field_info['choices'] = [
                {
                    'value': choice_value,
                    'display_name': force_str(choice_name, strings_only=True)
                }
                for choice_value, choice_name in field.choices.items()
            ]

        return field_info

    def set_styles_field(self, field_info, field):
        field_style = field.style
        if 'base_template' in field_style:
            field_style.pop('base_template', None)

        if field_style:
            field_info['style'] = field_style
