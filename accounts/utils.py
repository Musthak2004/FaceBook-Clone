from django.conf import settings
from django.core.mail import send_mail
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.template.loader import render_to_string
from django.urls import reverse

signer = TimestampSigner(salt="email-verify")


def generate_verification_token(user_id):
    """Generate a signed token for email verification."""
    return signer.sign(str(user_id))


def verify_token(token, max_age=86400):
    """Verify a signed token and return the user_id, or None if invalid."""
    try:
        user_id = signer.unsign(token, max_age=max_age)
        return int(user_id)
    except (BadSignature, SignatureExpired, ValueError):
        return None


def send_verification_email(request, user):
    """Send email verification link to a newly registered user."""
    token = generate_verification_token(user.pk)
    verify_url = request.build_absolute_uri(
        reverse("accounts:verify_email", kwargs={"token": token})
    )

    subject = "Verify your email — SocialNet"
    message = render_to_string(
        "accounts/verification_email.txt",
        {"user": user, "verify_url": verify_url},
    )
    html_message = render_to_string(
        "accounts/verification_email.html",
        {"user": user, "verify_url": verify_url},
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
