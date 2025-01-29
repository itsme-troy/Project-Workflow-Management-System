from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .utils import validate_email_with_abstract_api  # Import your validation function

User = get_user_model()

class EmailVerifiedBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = kwargs.get('email', username)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None
        
        # Check email validity via Abstract API
        if not validate_email_with_abstract_api(email):
            raise ValidationError("Invalid or non-existent email. Please check your email address.")

        if user.check_password(password):
            if not user.is_email_verified:
                raise ValidationError("Your email address is not verified.")
            if not user.is_active:
                raise ValidationError("Your account is inactive.")
            return user
        return None
