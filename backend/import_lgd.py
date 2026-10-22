import csv

from database import SessionLocal
from models import (
    State,
    District,
    SubDistrict,
    Place,
    PostalCode,
)


import sys

CSV_FILE = sys.argv[1] if len(sys.argv) > 1 else "data/telangana_villages.csv"


def import_lgd_data():
    db = SessionLocal()

    try:
        with open(
            CSV_FILE,
            "r",
            encoding="utf-8-sig"
        ) as file:

            reader = csv.DictReader(file)

            rows_processed = 0
            new_states = 0
            new_districts = 0
            new_subdistricts = 0
            new_places = 0
            new_postal_codes = 0

            for row in reader:

                rows_processed += 1

                # -------------------------
                # 1. STATE
                # -------------------------

                state_code = row["stateCode"].strip()
                state_name = row["stateNameEnglish"].strip()

                state = (
                    db.query(State)
                    .filter(State.lgd_code == state_code)
                    .first()
                )

                if not state:
                    state = State(
                        lgd_code=state_code,
                        name=state_name,
                        state_type="state"
                    )

                    db.add(state)
                    db.flush()

                    new_states += 1

                # -------------------------
                # 2. DISTRICT
                # -------------------------

                district_code = row["districtCode"].strip()
                district_name = row["districtNameEnglish"].strip()

                district = (
                    db.query(District)
                    .filter(
                        District.lgd_code == district_code
                    )
                    .first()
                )

                if not district:
                    district = District(
                        lgd_code=district_code,
                        name=district_name,
                        state_id=state.id
                    )

                    db.add(district)
                    db.flush()

                    new_districts += 1

                # -------------------------
                # 3. SUB-DISTRICT
                # -------------------------

                subdistrict_code = row[
                    "subdistrictCode"
                ].strip()

                subdistrict_name = row[
                    "subdistrictNameEnglish"
                ].strip()

                subdistrict = (
                    db.query(SubDistrict)
                    .filter(
                        SubDistrict.lgd_code
                        == subdistrict_code
                    )
                    .first()
                )

                if not subdistrict:
                    subdistrict = SubDistrict(
                        lgd_code=subdistrict_code,
                        name=subdistrict_name,
                        district_id=district.id
                    )

                    db.add(subdistrict)
                    db.flush()

                    new_subdistricts += 1

                # -------------------------
                # 4. VILLAGE / PLACE
                # -------------------------

                village_code = row[
                    "villageCode"
                ].strip()

                village_name = row[
                    "villageNameEnglish"
                ].strip()

                place = (
                    db.query(Place)
                    .filter(
                        Place.lgd_code == village_code
                    )
                    .first()
                )

                if not place:
                    place = Place(
                        lgd_code=village_code,
                        name=village_name,
                        place_type="village",
                        subdistrict_id=subdistrict.id
                    )

                    db.add(place)
                    db.flush()

                    new_places += 1

                # -------------------------
                # 5. PIN CODE
                # -------------------------

                pincode = row.get(
                    "pincode",
                    ""
                ).strip()

                if pincode:

                    existing_postal = (
                        db.query(PostalCode)
                        .filter(
                            PostalCode.pincode == pincode,
                            PostalCode.place_id == place.id
                        )
                        .first()
                    )

                    if not existing_postal:

                        postal_code = PostalCode(
                            pincode=pincode,
                            place_id=place.id
                        )

                        db.add(postal_code)

                        new_postal_codes += 1

            db.commit()

            print()
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("       LGD IMPORT COMPLETE")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print()
            print(f"Rows processed:       {rows_processed}")
            print(f"New states:           {new_states}")
            print(f"New districts:        {new_districts}")
            print(f"New subdistricts:     {new_subdistricts}")
            print(f"New villages:         {new_places}")
            print(f"New postal relations: {new_postal_codes}")
            print()
            print("✅ Import completed successfully!")
            print()

    except Exception as error:

        db.rollback()

        print()
        print("❌ Import failed:")
        print(error)
        print()

    finally:
        db.close()


if __name__ == "__main__":
    import_lgd_data()