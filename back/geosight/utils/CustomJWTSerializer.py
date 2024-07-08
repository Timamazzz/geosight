from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from users_app.models import User


class CustomJWTSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        credentials = {
            'email': '',
            'password': attrs.get("password")
        }

        # This is answering the original question, but do whatever you need here.
        # For example in my case I had to check a different model that stores more user info
        # But in the end, you should obtain the username to continue.
        user_obj = (User.objects.filter(email=attrs.get("email")).first() or
                    User.objects.filter(phone_number=attrs.get("email")).first())
        if user_obj:
            credentials['email'] = user_obj.email

        return super().validate(credentials)
