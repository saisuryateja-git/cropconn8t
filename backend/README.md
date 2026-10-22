# CropConn8t backend

This version uses the supplied Telangana LGD village dataset as the location master and Agmarknet for current commodity prices and market master data.

## Start

```bash
cd backend
/opt/anaconda3/bin/python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app
```

Do not use `--reload` until the project is stable; otherwise WatchFiles can observe `.venv` package installation changes.

## Key endpoints

- `GET /locations/districts?state=Telangana`
- `GET /locations/towns?district_id=734`
- `GET /locations/villages?subdistrict_code=...`
- `GET /locations/search?q=Achampet`
- `GET /locations/geocode?query=Achampet,Nagarkurnool`
- `GET /markets?district_id=734`
- `GET /prices?crop=maize&latitude=...&longitude=...&quantity_quintals=10&district_id=734`
- `GET /prices/general`

The `/prices` response contains current-price markets and an `alternatives` list that includes master-market entries even when today's crop price is unavailable.
