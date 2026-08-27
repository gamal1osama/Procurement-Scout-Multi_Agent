"""Unit tests for Pydantic domain models and DTOs."""

import pytest
from src.domain.procurement import ProcurementInput, ProcurementResult
from src.domain.product import AllExtractedProducts, ProductSpec, SingleExtractedProduct
from src.domain.search import AllSearchResults, SingleSearchResult, SuggestedSearchQueries


def test_suggested_search_queries():
    data = {"queries": ["site:www.amazon.eg espresso machine", "site:www.noon.com coffee maker"]}
    model = SuggestedSearchQueries(**data)
    assert len(model.queries) == 2
    assert "site:www.amazon.eg" in model.queries[0]


def test_search_results():
    single = SingleSearchResult(
        title="Espresso Maker 15 Bar",
        url="https://amazon.eg/dp/123",
        content="High quality espresso machine",
        score=0.88,
        search_query="site:amazon.eg espresso",
    )
    all_results = AllSearchResults(results=[single])
    assert len(all_results.results) == 1
    assert all_results.results[0].score == 0.88


def test_product_spec_and_extraction():
    spec1 = ProductSpec(specification_name="Power", specification_value="1450 W")
    spec2 = ProductSpec(specification_name="Pressure", specification_value="15 Bar")
    
    product = SingleExtractedProduct(
        page_url="https://noon.com/p/1",
        product_title="DeLonghi Dedica",
        product_image_url="https://img.noon.com/1.jpg",
        product_url="https://noon.com/p/1",
        is_available=True,
        product_current_price=8249.0,
        product_original_price=8855.0,
        product_discount_percentage=6.0,
        product_specs=[spec1, spec2],
        agent_recommendation_rank=5,
        agent_recommendation_notes=["Top rated compact espresso maker."],
    )
    
    all_prods = AllExtractedProducts(products=[product])
    assert len(all_prods.products) == 1
    assert all_prods.products[0].product_specs[0].specification_name == "Power"
    assert all_prods.products[0].agent_recommendation_rank == 5


def test_procurement_input_conversion():
    inp = ProcurementInput(
        product_name="espresso maker",
        websites_list=["www.amazon.eg"],
        country_name="Egypt",
        no_keywords=5,
        language="English",
        score_th=0.4,
        top_recommendations_no=10,
    )
    crew_dict = inp.to_crew_inputs()
    assert crew_dict["product_name"] == "espresso maker"
    assert crew_dict["no_keywords"] == 5
    assert crew_dict["score_th"] == 0.4
