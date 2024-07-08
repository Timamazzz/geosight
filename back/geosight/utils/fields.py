from rest_framework import serializers

PHONE_FIELD_DEFAULT_PLACEHOLDER = '+7'
PHONE_FIELD_DEFAULT_MASK = '+7 999 999-99-99'
PHONE_FIELD_DEFAULT_REGEX = ''
PHONE_FIELD_DEFAULT_LABEL = 'Номер телефона'


def formate_phone(phone):
    if not phone:
        return None

    digits_only = ''.join(filter(lambda x: x.isdigit(), phone))

    if len(digits_only) == 11 and digits_only.startswith('8'):
        digits_only = '+7' + digits_only[1:]

    formatted_phone = f'{digits_only[1:4]}{digits_only[4:7]}{digits_only[7:9]}{digits_only[9:]}'

    return formatted_phone


class PhoneField(serializers.CharField):

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.style = kwargs.get('style', {'placeholder': PHONE_FIELD_DEFAULT_PLACEHOLDER,
                                          'mask': PHONE_FIELD_DEFAULT_MASK})
        self.label = kwargs.get('label', PHONE_FIELD_DEFAULT_LABEL)

        if 'mask' in self.style:
            self.regex = kwargs.get('regex', PHONE_FIELD_DEFAULT_REGEX)


class PasswordField(serializers.CharField):
    def __init__(self, *args, **kwargs):
        min_length = kwargs.pop('min_length', 8)
        super().__init__(*args, **kwargs)
        self.min_length = min_length