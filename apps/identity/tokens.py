from django.core import signing


PASSWORD_RESET_SALT = "identity.password-reset"
EMAIL_VERIFICATION_SALT = "identity.email-verification"


def generate_password_reset_token(email: str) -> str:
    return signing.dumps({"email": email}, salt=PASSWORD_RESET_SALT)


def validate_password_reset_token(token: str, max_age: int = 60 * 60 * 24) -> str:
    payload = signing.loads(token, salt=PASSWORD_RESET_SALT, max_age=max_age)
    return payload["email"]


def generate_email_verification_token(email: str) -> str:
    return signing.dumps({"email": email}, salt=EMAIL_VERIFICATION_SALT)


def validate_email_verification_token(token: str, max_age: int = 60 * 60 * 24 * 7) -> str:
    payload = signing.loads(token, salt=EMAIL_VERIFICATION_SALT, max_age=max_age)
    return payload["email"]
