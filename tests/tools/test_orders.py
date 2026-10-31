"""Order lookup: identity from the session, and no difference between "someone else's" and "does not exist"."""

from app.tools.orders import get_order, list_profiles, resolve_profile


def test_profile_a_sees_order_8_shipped_with_tracking(snapshot_build):
    o = get_order(snapshot_build / "orders-demo.db", 2, 8)
    assert (o["found"], o["status"], o["total_cents"]) == (True, "shipped", 34990)
    assert o["tracking_code"] and o["estimated_delivery"] == "2026-02-28"
    assert o["items"] and all(set(i) == {"name", "quantity"} for i in o["items"])


def test_profile_b_sees_order_9_confirmed_without_tracking(snapshot_build):
    o = get_order(snapshot_build / "orders-demo.db", 6, 9)
    assert (o["status"], o["tracking_code"], o["estimated_delivery"]) == ("confirmed", None, None)


def test_cross_profile_equals_non_existent(snapshot_build):
    db = snapshot_build / "orders-demo.db"
    assert get_order(db, 6, 8) == get_order(db, 6, 999) == get_order(db, 6, 1)
    assert get_order(db, 6, 8)["found"] is False


def test_visitor_needs_profile(snapshot_build):
    assert get_order(snapshot_build / "orders-demo.db", None, 8)["error"] == "profile_required"


def test_profiles_are_aliases_only(snapshot_build):
    db = snapshot_build / "orders-demo.db"
    profiles = list_profiles(db)
    assert [p["alias"] for p in profiles] == ["demo-a", "demo-b", "demo-c"]
    assert all(set(p) == {"alias", "label"} for p in profiles)
    assert resolve_profile(db, "demo-a") == 2 and resolve_profile(db, "' OR 1=1 --") is None
