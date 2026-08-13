import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom email-based User model. Single source of truth that every other
    Sinevest Premium app (Wallet, KYCProfile, TransactionPin, Trade, etc.)
    relates back to.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(
        unique=True,
        help_text="User's unique email address. Used as the login identifier.",
    )
    first_name = models.CharField(max_length=150, help_text="User's first name.")
    last_name = models.CharField(max_length=150, help_text="User's last name.")
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether the user has confirmed their email address via OTP.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text=(
            "Designates whether this account is active. Admins toggling this off "
            "blocks state-changing actions across the platform, but does NOT block login."
        ),
    )
    is_staff = models.BooleanField(
        default=False,
        help_text="Designates whether the user can access the Django admin site.",
    )
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name


class OTP(models.Model):
    """
    Short-lived one-time-passcode used for registration email verification.
    (password_reset kept as a reserved purpose choice — the actual password
    reset flow below uses a signed token, not an OTP.)
    """

    PURPOSE_CHOICES = (
        ("register", "Register"),
        ("password_reset", "Password Reset"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="otps",
        help_text="The user this OTP was issued to.",
    )
    code = models.CharField(max_length=6, help_text="6-digit zero-padded numeric OTP code.")
    purpose = models.CharField(
        max_length=20, choices=PURPOSE_CHOICES, default="register", help_text="What this OTP is for."
    )
    is_used = models.BooleanField(default=False, help_text="Whether this OTP has already been consumed.")
    expires_at = models.DateTimeField(help_text="Moment after which this OTP is no longer valid.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "OTP"
        verbose_name_plural = "OTPs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.purpose} - {self.code}"

    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()


class PasswordResetToken(models.Model):
    """
    Signed, single-use token used to authorize a password reset. The `id`
    (UUID) doubles as the identifier sent in the reset link; `token` is the
    hashed raw token, never stored in plaintext.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
        help_text="The user requesting the password reset.",
    )
    token = models.CharField(
        max_length=255, help_text="Hashed reset token (stored via Django's make_password)."
    )
    is_used = models.BooleanField(default=False, help_text="Whether this token has already been consumed.")
    expires_at = models.DateTimeField(help_text="Moment after which this token is no longer valid.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Password Reset Token"
        verbose_name_plural = "Password Reset Tokens"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - reset token - {self.id}"

    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()