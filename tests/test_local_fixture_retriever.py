from app.services.retriever import Fixture, LocalFixtureRetriever


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
