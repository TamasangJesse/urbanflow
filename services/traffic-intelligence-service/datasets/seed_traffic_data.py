"""
seed_traffic_data.py
UrbanFlow — Traffic Intelligence Service
-----------------------------------------
Run ONCE before starting the Traffic Intelligence Service.

Flow:
  1. python seed_traffic_data.py        ← you run this
  2. uvicorn main:app --reload          ← service starts, calls train_model() automatically
  3. GET /predict  →  reads model.pkl   ← live predictions

Usage:
  DB credentials can be supplied via environment variables or by editing
  the DB_CONFIG dict below.

  Environment variables (take priority over DB_CONFIG):
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD

Requirements:
  pip install psycopg2-binary
"""

import os
import random
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Load .env from the project root — same file the FastAPI app reads
# This guarantees seed_traffic_data.py and the app always use identical credentials
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# ---------------------------------------------------------------------------
# 1. DATABASE CONFIG
#    Read from DATABASE_URL in .env — single source of truth.
#    The host must be 'db' when running inside Docker (matches docker-compose service name).
#    Use 'localhost' only if running the seed script directly on the VPS host outside Docker.
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. "
        "Make sure .env exists at the project root with: "
        "DATABASE_URL=postgresql://urbanflow:yourpassword@db:5432/urbanflow_traffic"
    )

# ---------------------------------------------------------------------------
# 2. YAOUNDÉ LOCATIONS — 19 real traffic hotspots
#
#    busyness  — congestion bias multiplier:
#      < 1.0   → inherently quieter (diplomatic, residential)
#      1.0     → average
#      1.1–1.2 → moderately busy (mixed residential/commercial)
#      1.3–1.4 → busy (markets, major intersections)
#      1.5+    → very busy (CBD, biggest markets, key roundabouts)
#
#    special   — locations with an EXTRA spike at specific hours/days
#                boost: pushes congestion index up N levels (clamped to 3)
# ---------------------------------------------------------------------------
LOCATIONS = [
    # ── Your original list ──────────────────────────────────────────────────
    {
        "name": "Obili",
        "lat": 3.8601, "lng": 11.4972,
        "busyness": 1.2,
        "notes": "Student zone near university, heavy morning commuter traffic",
        "special": {
            "hour_range": (7, 10),
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "boost": 1,
        },
    },
    {
        "name": "Carrefour Emia",
        "lat": 3.8752, "lng": 11.5043,
        "busyness": 1.3,
        "notes": "Classic congestion roundabout, central node",
        "special": None,
    },
    {
        "name": "Rond Point Express",
        "lat": 3.8698, "lng": 11.5201,
        "busyness": 1.5,
        "notes": "One of the busiest intersections in Yaoundé",
        "special": None,
    },
    {
        "name": "Dispensaire Messassi",
        "lat": 3.8541, "lng": 11.5367,
        "busyness": 1.1,
        "notes": "Neighbourhood landmark, moderate residential traffic",
        "special": None,
    },
    {
        "name": "Etoudi",
        "lat": 3.9021, "lng": 11.5298,
        "busyness": 1.2,
        "notes": "Presidential quarter — notable congestion, especially during motorcades",
        "special": {
            "hour_range": (8, 10),
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "boost": 1,
        },
    },
    {
        "name": "Total Melen",
        "lat": 3.8634, "lng": 11.5089,
        "busyness": 1.3,
        "notes": "Fuel station landmark — key intersection, heavy mixed traffic",
        "special": None,
    },
    {
        "name": "Bastos",
        "lat": 3.8830, "lng": 11.5150,
        "busyness": 0.85,
        "notes": "Diplomatic/expat zone — quieter but morning embassy rush notable",
        "special": {
            "hour_range": (7, 9),
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "boost": 1,
        },
    },
    {
        "name": "Carrefour Warda",
        "lat": 3.8731, "lng": 11.5321,
        "busyness": 1.4,
        "notes": "Very busy commercial carrefour, all-day congestion",
        "special": None,
    },
    {
        "name": "Entree Simbock",
        "lat": 3.8289, "lng": 11.4901,
        "busyness": 1.3,
        "notes": "Southern entry corridor, heavy commuter inflow/outflow",
        "special": {
            "hour_range": (17, 20),
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "boost": 1,
        },
    },

    # ── Recommended additions ────────────────────────────────────────────────
    {
        "name": "Mokolo Market",
        "lat": 3.8784, "lng": 11.5058,
        "busyness": 1.6,
        "notes": "Busiest market in Yaoundé — peak congestion all morning and midday",
        "special": {
            "hour_range": (8, 14),
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
            "boost": 1,
        },
    },
    {
        "name": "Carrefour Nlongkak",
        "lat": 3.8876, "lng": 11.5212,
        "busyness": 1.2,
        "notes": "Major intersection linking several residential zones",
        "special": None,
    },
    {
        "name": "Mimboman",
        "lat": 3.8512, "lng": 11.5512,
        "busyness": 1.3,
        "notes": "High-traffic node — targeted by 2026 government road upgrades",
        "special": None,
    },
    {
        "name": "Emana",
        "lat": 3.9187, "lng": 11.5423,
        "busyness": 1.35,
        "notes": "Major congestion point on Route Nationale 1, heavy logging truck traffic",
        "special": {
            "hour_range": (6, 9),
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "boost": 1,
        },
    },
    {
        "name": "Nkoabang",
        "lat": 3.9312, "lng": 11.5589,
        "busyness": 1.2,
        "notes": "RN1 corridor congestion point, commuter and freight traffic",
        "special": None,
    },
    {
        "name": "Biyem-Assi",
        "lat": 3.8469, "lng": 11.4938,
        "busyness": 1.15,
        "notes": "Large dense residential zone, heavy morning rush",
        "special": {
            "hour_range": (7, 9),
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "boost": 1,
        },
    },
    {
        "name": "Nsimalen Road",
        "lat": 3.7823, "lng": 11.5134,
        "busyness": 1.1,
        "notes": "Airport corridor — heavy morning taxi and commuter traffic",
        "special": {
            "hour_range": (6, 9),
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            "boost": 1,
        },
    },
    {
        "name": "Mvog-Ada",
        "lat": 3.8512, "lng": 11.5298,
        "busyness": 1.2,
        "notes": "Market + residential mix, classic congestion zone",
        "special": None,
    },
    {
        "name": "Hippodrome",
        "lat": 3.8716, "lng": 11.5094,
        "busyness": 1.1,
        "notes": "Central area, event traffic from government functions",
        "special": {
            "hour_range": (17, 21),
            "days": ["Friday", "Saturday"],
            "boost": 1,
        },
    },
    {
        "name": "Omnisports",
        "lat": 3.8743, "lng": 11.5167,
        "busyness": 1.0,
        "notes": "Stadium zone — extreme traffic on match evenings",
        "special": {
            "hour_range": (17, 22),
            "days": ["Friday", "Saturday", "Sunday"],
            "boost": 2,
        },
    },
]

DAYS_OF_WEEK      = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
CONGESTION_LEVELS = ["Low", "Medium", "High", "Very High"]

# ---------------------------------------------------------------------------
# 3. NOISE CONFIG
#    12 % sits comfortably in the 10–15 % window.
#    Noise shifts a label ±1 level (not a full random jump) — realistic, not chaotic.
# ---------------------------------------------------------------------------
NOISE_RATE             = 0.12
SAMPLES_PER_COMBINATION = 2
# 19 locations × 7 days × 24 hours × 2 samples = 6,384 rows  ✓ (well under 8,000)

# ---------------------------------------------------------------------------
# 4. RULE-BASED CONGESTION LOGIC
# ---------------------------------------------------------------------------

def _base_congestion_index(hour: int, day: str, busyness: float) -> int:
    """
    Returns 0–3 mapping to Low / Medium / High / Very High.
    Encodes real Yaoundé patterns before location specials and noise.
    """
    is_weekend = day in ("Saturday", "Sunday")

    if hour >= 21 or hour < 5:      # Night
        return 0

    if 5 <= hour < 7:               # Early morning
        return 0 if is_weekend else 1

    if 7 <= hour < 10:              # Morning rush
        if is_weekend:
            return 1
        return 3 if busyness >= 1.4 else 2

    if 10 <= hour < 11:             # Mid-morning lull
        return 1 if is_weekend else 2

    if 11 <= hour < 14:             # Midday
        if is_weekend:
            return 1
        return 3 if busyness >= 1.4 else 2

    if 14 <= hour < 17:             # Afternoon lull
        return 1

    if 17 <= hour < 20:             # Evening rush
        if is_weekend:
            return 1
        return 3 if busyness >= 1.2 else 2

    return 0 if is_weekend else 1   # Late evening (8–9 pm)


def assign_congestion(hour: int, day: str, location: dict) -> str:
    """
    Returns a final congestion label, applying in order:
      1. Base rule  (hour / day / busyness)
      2. Location special boost  (if hour+day match the peak window)
      3. 12 % noise  (±1 level shift)
    """
    idx = _base_congestion_index(hour, day, location["busyness"])

    special = location.get("special")
    if special:
        h_start, h_end = special["hour_range"]
        if h_start <= hour < h_end and day in special["days"]:
            idx = min(3, idx + special["boost"])

    if random.random() < NOISE_RATE:
        shift = random.choice([-1, 1])
        idx   = max(0, min(3, idx + shift))

    return CONGESTION_LEVELS[idx]


# ---------------------------------------------------------------------------
# 5. ROW GENERATION
# ---------------------------------------------------------------------------

def generate_rows() -> list[tuple]:
    rows = []
    for location in LOCATIONS:
        for day in DAYS_OF_WEEK:
            for hour in range(24):
                for _ in range(SAMPLES_PER_COMBINATION):
                    congestion = assign_congestion(hour, day, location)
                    rows.append((
                        location["name"],   # location_name
                        location["lat"],    # latitude
                        location["lng"],    # longitude
                        day,                # day_of_week
                        hour,               # hour
                        congestion,         # congestion_level
                        "simulated",        # source
                    ))

    random.shuffle(rows)
    return rows


# ---------------------------------------------------------------------------
# 6. DATABASE SETUP + INSERTION
# ---------------------------------------------------------------------------

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS traffic_data (
    id               SERIAL PRIMARY KEY,
    location_name    VARCHAR(100)       NOT NULL,
    latitude         DOUBLE PRECISION   NOT NULL,
    longitude        DOUBLE PRECISION   NOT NULL,
    day_of_week      VARCHAR(10)        NOT NULL,
    hour             SMALLINT           NOT NULL CHECK (hour >= 0 AND hour <= 23),
    congestion_level VARCHAR(20)        NOT NULL,
    source           VARCHAR(30)        NOT NULL DEFAULT 'simulated',
    created_at       TIMESTAMPTZ        NOT NULL DEFAULT NOW()
);
"""

INSERT_SQL = """
INSERT INTO traffic_data
    (location_name, latitude, longitude, day_of_week, hour, congestion_level, source)
VALUES %s
"""


def seed():
    target = len(LOCATIONS) * 7 * 24 * SAMPLES_PER_COMBINATION
    print("=" * 64)
    print("  UrbanFlow — Traffic Intelligence Seed Script")
    print(f"  {len(LOCATIONS)} locations  |  target {target:,} rows")
    print("=" * 64)

    # ── Connect ──────────────────────────────────────────────────────────────
    print(f"\n[1/4] Connecting to PostgreSQL ...")
    print(f"      {DATABASE_URL.split('@')[-1]}")
    try:
        conn = psycopg2.connect(dsn=DATABASE_URL)
        conn.autocommit = False
        cur  = conn.cursor()
        print("      Connected ✓")
    except psycopg2.OperationalError as e:
        print(f"\n  ERROR: Could not connect to PostgreSQL.\n  {e}")
        print("\n  Check DATABASE_URL in your .env file.")
        raise SystemExit(1)

    # ── Create table ─────────────────────────────────────────────────────────
    print("\n[2/4] Creating traffic_data table (if not exists) ...")
    cur.execute(CREATE_TABLE_SQL)
    conn.commit()
    print("      Table ready ✓")

    # ── Guard against double-seeding ─────────────────────────────────────────
    cur.execute("SELECT COUNT(*) FROM traffic_data WHERE source = 'simulated';")
    existing = cur.fetchone()[0]
    if existing > 0:
        print(f"\n  WARNING: {existing:,} simulated rows already exist in traffic_data.")
        answer = input("  Re-seed anyway? This will ADD more rows. (yes/no): ").strip().lower()
        if answer != "yes":
            print("  Aborted — no rows inserted.")
            cur.close(); conn.close()
            raise SystemExit(0)

    # ── Generate ─────────────────────────────────────────────────────────────
    print("\n[3/4] Generating synthetic traffic records ...")
    random.seed(42)   # reproducible — same seed → same dataset every run
    rows = generate_rows()
    print(f"      Generated {len(rows):,} rows ✓")

    # ── Insert ───────────────────────────────────────────────────────────────
    print("\n[4/4] Inserting into PostgreSQL ...")
    try:
        execute_values(cur, INSERT_SQL, rows, page_size=500)
        conn.commit()
        print(f"      Inserted {len(rows):,} rows ✓")
    except Exception as e:
        conn.rollback()
        print(f"\n  ERROR during insert: {e}")
        cur.close(); conn.close()
        raise SystemExit(1)

    # ── Summary ───────────────────────────────────────────────────────────────
    cur.execute("""
        SELECT congestion_level, COUNT(*)
        FROM   traffic_data
        GROUP  BY congestion_level
        ORDER  BY CASE congestion_level
            WHEN 'Low'       THEN 1
            WHEN 'Medium'    THEN 2
            WHEN 'High'      THEN 3
            WHEN 'Very High' THEN 4
        END;
    """)
    print("\n  Congestion distribution in DB:")
    total = len(rows)
    for level, count in cur.fetchall():
        pct = count / total * 100
        bar = "█" * int(pct / 2)
        print(f"    {level:<12}  {count:>5} rows  ({pct:4.1f}%)  {bar}")

    print("\n  Locations seeded:")
    for loc in LOCATIONS:
        tag = "⚡" if loc["special"] else "  "
        print(f"    {tag} {loc['name']:<28}  busyness={loc['busyness']}  — {loc['notes']}")

    cur.close()
    conn.close()
    print(
        "\n  All done! Start the Traffic Intelligence Service — it will\n"
        "  call train_model() on startup and read from this data.\n"
        "\n  ⚡ = location has a special peak-hour boost\n"
    )


if __name__ == "__main__":
    seed()