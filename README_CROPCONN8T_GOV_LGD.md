# CropConn8t — Government LGD + Agmarknet Market Architecture

This replacement project makes the supplied Telangana LGD dataset the location master and Agmarknet the market/price source.

## Location architecture

LGD CSV → District → Mandal/Subdistrict → Village → Pincode

Agmarknet → APMC/market master → current crop prices

Nominatim → coordinates for selected farmer location and market alternatives

Recommendation engine → price + distance + transport + farmer quantity + market activity

## Important behavior

- The location dropdowns are sourced from `backend/data/telangana_villages.csv`.
- `Nagarkurnool` maps to Agmarknet district ID `734` and LGD district code `694`.
- `/locations/towns?district_id=734` returns the 20 Nagarkurnool mandals/subdistricts from the LGD dataset.
- `/locations/villages?subdistrict_code=4579` returns Achampet villages from LGD.
- `/prices` returns both current-price markets and `alternatives`; alternatives can have `current_price_available=false` when the market exists in the master list but today's crop price was not reported.
- A market more than 100 km away is not treated as a normal nearby winner. The recommendation engine only selects a best economic market within 100 km, otherwise up to 200 km as `FAR_BUT_BEST_AVAILABLE`; beyond that it returns no suitable best market.

## Environment

Copy your existing government API key into `backend/.env`:

```env
DATA_GOV_API_KEY=YOUR_DATA_GOV_API_KEY
TRANSPORT_COST_PER_KM_PER_QUINTAL=2.50
TRANSPORT_FIXED_TRIP_COST=0
DEFAULT_FARMER_QUANTITY_QUINTALS=10
SOFT_DISTANCE_LIMIT_KM=100
HARD_DISTANCE_LIMIT_KM=200
```

The ZIP intentionally does not contain a real secret key.

## Backend

```bash
cd backend
/opt/anaconda3/bin/python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app
```

Run without `--reload` for now so WatchFiles does not monitor the virtual environment.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

The agricultural video remains at:

`frontend/src/assets/agriculturevid.mp4`
