"""Tests for data loading, indexing, and query operations."""


def test_load_counts(mini_db):
    assert len(mini_db.items) == 6
    assert len(mini_db.functions) == 5
    assert len(mini_db.families) == 2
    assert len(mini_db.compounds) == 1


def test_reverse_indexes(mini_db):
    assert mini_db.by_inci["AQUA"] == "75528"
    assert "87220" in mini_db.by_cas["90106-38-0"]
    assert "87220" in mini_db.by_species["Rosa damascena"]
    assert "87220" in mini_db.by_family[0]


def test_lookup_by_ref(mini_db):
    r = mini_db.lookup("87220")
    assert r is not None
    assert r["inci_name"] == "ROSA DAMASCENA BUD EXTRACT"
    assert r["species"] == "Rosa damascena"
    assert r["family"] == "Rosaceae"
    assert "explorer_url" in r


def test_lookup_by_cas(mini_db):
    r = mini_db.lookup("56-81-5")
    assert r is not None
    assert r["inci_name"] == "GLYCERIN"


def test_lookup_by_inci(mini_db):
    r = mini_db.lookup("aqua")
    assert r is not None
    assert r["ref_no"] == "75528"


def test_lookup_not_found(mini_db):
    assert mini_db.lookup("DOES_NOT_EXIST") is None


def test_search_basic(mini_db):
    results = mini_db.search("rosa")
    assert len(results) >= 1
    assert any(r["ref_no"] == "87220" for r in results)


def test_search_bio_only(mini_db):
    results = mini_db.search("a", bio_only=True)
    for r in results:
        assert "species" in r


def test_search_restricted_only(mini_db):
    results = mini_db.search("a", restricted_only=True)
    for r in results:
        assert "restriction" in r


def test_get_species(mini_db):
    r = mini_db.get_species_info("Rosa damascena")
    assert r is not None
    assert r["extract_count"] == 1
    assert r["common_name_zh"] == "大馬士革玫瑰"
    assert r["family"] == "Rosaceae"
    assert len(r["extracts"]) == 1


def test_get_species_not_found(mini_db):
    assert mini_db.get_species_info("Fake species") is None


def test_get_family(mini_db):
    r = mini_db.get_family_info("Rosaceae")
    assert r is not None
    assert r["species_count"] == 1
    assert r["extract_count"] == 1
    assert r["common_name_zh"] == "薔薇科"
    assert len(r["top_functions"]) >= 1


def test_get_family_case_insensitive(mini_db):
    r = mini_db.get_family_info("rosaceae")
    assert r is not None
    assert r["family"] == "Rosaceae"


def test_get_family_not_found(mini_db):
    assert mini_db.get_family_info("Fakaceae") is None


def test_get_regulation_restricted(mini_db):
    r = mini_db.get_regulation("31464")
    assert r["restriction_text"] == "II/1254"
    assert r["parsed"]["annex"] == "II (Prohibited)"
    assert r["parsed"]["entry"] == "1254"


def test_get_regulation_no_restriction(mini_db):
    r = mini_db.get_regulation("75528")
    assert r["restriction"] is None


def test_get_regulation_not_found(mini_db):
    assert mini_db.get_regulation("99999") is None


def test_analyze_list(mini_db):
    r = mini_db.analyze_list(["AQUA", "GLYCERIN", "ROSA DAMASCENA BUD EXTRACT", "FAKESTUFF"])
    assert r["summary"]["matched_count"] == 3
    assert r["summary"]["unmatched_count"] == 1
    assert r["summary"]["bio_source_count"] == 1
    assert "FAKESTUFF" in r["unmatched"]
    assert len(r["matched"]) == 3


def test_analyze_list_empty(mini_db):
    r = mini_db.analyze_list([])
    assert r["summary"]["total"] == 0


def test_explorer_url_format(mini_db):
    r = mini_db.lookup("87220")
    assert "?ingredient=87220" in r["explorer_url"]
