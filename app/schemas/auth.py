from typing import Literal

from pydantic import BaseModel, Field, model_validator


class LoginRequest(BaseModel):
    profile: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class SessionRead(BaseModel):
    authenticated: bool
    profile: str


class RegisterRequest(BaseModel):
    profile: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9._-]+$")
    full_name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=254)
    phone: str | None = Field(default=None, max_length=24)
    preferred_currency: Literal["EUR", "USD", "GBP", "CHF"] = "EUR"
    password: str = Field(min_length=10, max_length=256)
    password_confirmation: str = Field(min_length=10, max_length=256)
    accepted_terms: bool

    @model_validator(mode="after")
    def validate_registration(self) -> "RegisterRequest":
        local, separator, domain = self.email.strip().partition("@")
        if not separator or not local or "." not in domain:
            raise ValueError("A valid email address is required.")
        if self.password != self.password_confirmation:
            raise ValueError("Passwords do not match.")
        if not self.accepted_terms:
            raise ValueError("Terms and privacy policy must be accepted.")
        return self
