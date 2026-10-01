from rest_framework.throttling import AnonRateThrottle


class RegistrationThrottle(AnonRateThrottle):
    scope = "auth_register"
    rate = "5/hour"


class LoginThrottle(AnonRateThrottle):
    scope = "auth_login"
    rate = "10/minute"


class RefreshTokenThrottle(AnonRateThrottle):
    scope = "auth_refresh"
    rate = "20/minute"


class VerificationThrottle(AnonRateThrottle):
    scope = "auth_verify"
    rate = "20/hour"


class VerificationResendThrottle(AnonRateThrottle):
    scope = "auth_verify_resend"
    rate = "5/hour"


class PasswordResetRequestThrottle(AnonRateThrottle):
    scope = "auth_password_reset_request"
    rate = "5/hour"


class PasswordResetConfirmThrottle(AnonRateThrottle):
    scope = "auth_password_reset_confirm"
    rate = "10/hour"


class ContactThrottle(AnonRateThrottle):
    scope = "public_contact"
    rate = "5/hour"
