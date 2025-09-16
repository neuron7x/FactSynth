import pytest
from pydantic import ValidationError

from factsynth_ultimate.schemas.requests import DomainMetadata, ScoreReq

def test_domain_metadata_valid():
    meta = DomainMetadata(
        region="us",
        language="en",
        time_range="2020-01-01/2020-12-31",
    )
    req = ScoreReq(text="t", domain=meta)
    assert req.domain == meta

def test_domain_metadata_invalid_region_code():
    with pytest.raises(ValidationError):
        DomainMetadata(region="zz", language="en", time_range="2020-01-01/2020-12-31")

def test_domain_metadata_invalid_language_code():
    with pytest.raises(ValidationError):
        DomainMetadata(region="US", language="zz", time_range="2020-01-01/2020-12-31")

def test_domain_metadata_malformed_time_range_string():
    with pytest.raises(ValidationError):
        DomainMetadata(region="US", language="en", time_range="2020")

def test_domain_metadata_malformed_time_range_object():
    with pytest.raises(ValidationError):
        DomainMetadata(
            region="US",
            language="en",
            time_range={"start": "2020-01-01"},
        )

def test_domain_metadata_invalid_region_format():
    with pytest.raises(ValidationError):
        DomainMetadata(region="USA", language="en", time_range="2020-01-01/2020-12-31")

def test_domain_metadata_time_range_end_before_start():
    with pytest.raises(ValidationError):
        DomainMetadata(region="US", language="en", time_range="2020-12-31/2020-01-01")

