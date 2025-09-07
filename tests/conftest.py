import pydantic

# Provide a minimal stub for BaseSettings to avoid requiring pydantic-settings.
# This is sufficient for tests which only rely on attribute defaults.
pydantic.BaseSettings = object  # type: ignore
