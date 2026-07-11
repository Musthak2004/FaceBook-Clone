from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode


def generate_verification_token(user):
    """Generate uid and token for email verification."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return uid, token


def verify_token(uidb64, token):
    """Verify a token and return the user if valid, else None."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None
    if user is not None and default_token_generator.check_token(user, token):
        return user
    return None


def send_verification_email(request, user):
    """Send email verification link to the user."""
    uid, token = generate_verification_token(user)
    verification_url = reverse('verify_email', kwargs={'uidb64': uid, 'token': token})
    full_url = f"{request.scheme}://{request.get_host()}{verification_url}"
    mail_subject = 'Verify your email address'
    message = (
        f'Hi {user.username},\n\n'
        f'Thank you for creating an account. Please click the link below '
        f'to verify your email address:\n\n{full_url}\n\n'
        f'If you did not create this account, please ignore this email.'
    )
    email = EmailMessage(mail_subject, message, to=[user.email])
    email.send()
