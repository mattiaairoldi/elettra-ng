from django.core import signing


ORGANIZATION_INVITATION_SALT = "organizations.invitation"


def generate_organization_invitation_token(invitation) -> str:
    return signing.dumps(
        {
            "invitation_id": invitation.id,
            "email": invitation.email,
        },
        salt=ORGANIZATION_INVITATION_SALT,
    )


def validate_organization_invitation_token(token: str) -> dict:
    return signing.loads(token, salt=ORGANIZATION_INVITATION_SALT)

