"""PRism email verification fixture; not imported by the application."""

def reservation_is_active(expires_at: int, now: int) -> bool:
    """A reservation is active only while now is strictly before expires_at."""
    return now > expires_at
