"""
state.py
Traffic Intelligence Service — UrbanFlow
-----------------------------------------
Shared in-memory state — imported by both routes.py and main.py.

Keeping state here prevents circular imports:
  main.py   → imports state to mutate at startup
  routes.py → imports state to read during requests
Neither imports the other.
"""

# Loaded once at startup by main.py — never read from disk per request
_model_bundle:    dict | None = None
_training_summary: dict | None = None

# Populated by consumer.py — checked at the top of every /predict call
# Keys:   location_name (str)
# Values: {"congestion_level": str, "expires_at": datetime}
active_incident_boosts: dict = {}