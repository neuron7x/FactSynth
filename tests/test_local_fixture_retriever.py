import pytest

from factsynth_ultimate.services.retriever import (
    Fixture,
    LocalFixtureRetriever,
)


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
def test_ukrainian_query_matches_english_fixture():
    fixtures = [
        Fixture(id="en1", text="Microservices allow independent deployment."),
        Fixture(id="en2", text="Monolithic applications are single large services."),
    ]
    retriever = LocalFixtureRetriever(fixtures)

    results = retriever.search("Що таке мікросервіси?", k=1)
    assert results, "No results returned"
    top_doc = results[0]
    assert top_doc.id == "en1"
    assert top_doc.score > 0


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
@pytest.mark.parametrize(
    "query, expected_id, expected_translation",
    [
        ("Як працює мікросервіс?", "en_microservice", "microservice"),
        ("Що таке хмара?", "en_cloud", "cloud"),
    ],
)
def test_ukrainian_keywords_translated(query, expected_id, expected_translation):
    fixtures = [
        Fixture(
            id="en_microservice",
            text="A microservice is an independently deployable component.",
        ),
        Fixture(
            id="en_cloud",
            text="Cloud platforms provide scalable resources over the internet.",
        ),
    ]
    retriever = LocalFixtureRetriever(fixtures)

    results = retriever.search(query, k=1)
    assert results, "No results returned"

    # Ensure expected substitution happened before tokenization.
    assert expected_translation in retriever._translate_query(query)

    top_doc = results[0]
    assert top_doc.id == expected_id
    assert top_doc.score > 0
