from services.lgd import district_list, subdistricts_for_lgd_district, villages_for_subdistrict


def test_lgd_dataset():
    assert len(district_list()) == 33
    nag = subdistricts_for_lgd_district("694")
    assert len(nag) == 20
    assert any(x["subdistrict_name"] == "Achampet" for x in nag)
    ach = next(x for x in nag if x["subdistrict_name"] == "Achampet")
    villages = villages_for_subdistrict(ach["subdistrict_code"])
    assert len(villages) > 0


if __name__ == "__main__":
    test_lgd_dataset()
    print("LGD location smoke test passed")
