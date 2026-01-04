from datetime import datetime, timezone as datetime_timezone
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

class JWTLogoutAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)

        iat = validated_token.get("iat")
        if iat is None:
            return user

        issued_at = datetime.fromtimestamp(iat, tz=datetime_timezone.utc)

        invalid_before = getattr(user.profile, "token_invalid_before", None)
        if invalid_before and issued_at <= invalid_before:
            raise InvalidToken("Token is no longer valid (user logged out).")

        return user