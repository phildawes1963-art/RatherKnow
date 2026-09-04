import sys, os
import asyncio
import uuid
import random
import sys
import httpx
from fastapi import FastAPI
from routes.mirror_v2 import router
from auth import router as auth_router, ensure_indexes

app = FastAPI()
app.include_router(router)
app.include_router(auth_router)
random.seed(7)

AUTH_HEADERS = {}


async def flow(c, instrument, n_items, values):
    s = (await c.post("/api/v2/assessments", json={"instrument": instrument}, headers=AUTH_HEADERS)).json()
    sid = s["session_id"]
    assert len(s["items"]) == n_items, (instrument, len(s["items"]))
    batch = [{"item_id": it["id"], "value": values(it), "ms": 800} for it in s["items"]]
    r = await c.put(f"/api/v2/assessments/{sid}/responses", json={"responses": batch}, headers=AUTH_HEADERS)
    assert r.json()["saved"] == n_items, r.text
    res = await c.post(f"/api/v2/assessments/{sid}/complete", headers=AUTH_HEADERS)
    assert res.status_code == 200, res.text[:300]
    return sid, res.json()


async def main():
    await ensure_indexes()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://rk") as c:
        # Register a throwaway user (or login if it already exists) for the gated instruments
        email = f"e2e+{uuid.uuid4().hex[:12]}@ratherknow.com"
        reg = await c.post("/api/auth/register", json={
            "name": "E2E User", "email": email, "password": "knowmore123",
            "situation": "single_dating",
        })
        assert reg.status_code == 200, reg.text[:300]
        token = reg.json()["access_token"]
        AUTH_HEADERS["Authorization"] = f"Bearer {token}"
        sid_e, ess = await flow(c, "essential", 100, lambda it: random.randint(1, 5))
        assert ess["self"]["primary"]["name"] and "delta" in ess
        sid_p, per = await flow(c, "personality", 130, lambda it: random.randint(1, 5))
        assert len(per["factor_scores"]) == 15 and per["global_scores"]
        sid_q, eq = await flow(c, "eq", 140, lambda it: random.randint(1, 5))
        assert eq["overall_score"] and len(eq["domain_scores"]) == 4
        sid_c, clo = await flow(c, "closeness", 37, lambda it: random.randint(1, 7))
        assert "dimensions" in clo

        f = (await c.post("/api/v2/mirrors/findings", json={"session_ids": [sid_e, sid_p, sid_q, sid_c]}, headers=AUTH_HEADERS)).json()
        assert sorted(f["instruments_complete"]) == ["closeness", "eq", "essential", "personality"]

        r = (await c.post("/api/v2/reflections")).json()
        rid = r["reflection_id"]
        await c.put(f"/api/v2/reflections/{rid}/responses", json={"responses": [
            {"item_id": f"f{i}", "value": ((i - 1) % 4) + 1} for i in range(1, 9)
        ] + [{"item_id": "f-safety", "value": 1}]})
        fr = (await c.post(f"/api/v2/reflections/{rid}/complete")).json()
        assert fr["kind"] == "flag_check" and "pattern" in fr and "score" not in fr

        print("PACKAGED E2E OK —",
              "essential delta", ess["delta"]["overall"], "|",
              "personality factors", len(per["factor_scores"]), "|",
              "eq overall", eq["overall_score"], "|",
              "closeness conf", clo.get("confidence"), "|",
              "findings", len(f["findings"]), "|",
              "flag pattern", fr["pattern"])


asyncio.run(main())
