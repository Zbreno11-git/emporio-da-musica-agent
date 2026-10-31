"""Cost model arithmetic on synthetic usage rows: the numbers in the delivery PDF must be recomputable by hand."""

from __future__ import annotations

import json

import pytest

from scripts import cost_model

PRICE = {"input_per_mtok": 0.25, "output_per_mtok": 1.50}


def row(turn_type, inp, out, thoughts, seconds=2.0, scenario="x", step=0, repeat=1):
    return {"turn_type": turn_type, "usage": {"input": inp, "output": out, "thoughts": thoughts},
            "seconds": seconds, "model_calls": 2, "scenario": scenario, "step": step, "repeat": repeat}


def test_cost_per_turn_bills_thinking_tokens_as_output():
    rows = [row("quote", 6000, 100, 0), row("policy", 4000, 100, 200)]
    stats = cost_model.turn_stats(rows, PRICE)
    # quote: 6000*0.25 + 100*1.50 = 1650 µUSD; policy: 4000*0.25 + 300*1.50 = 1450 µUSD
    assert stats["by_type"]["quote"]["avg_usd"] == pytest.approx(0.00165)
    assert stats["by_type"]["policy"]["avg_usd"] == pytest.approx(0.00145)
    assert stats["mean_usd"] == pytest.approx(0.00155)
    assert stats["max_usd"] == pytest.approx(0.00165)


def test_monthly_projection_is_mean_times_turns_times_conversations():
    assert cost_model.gemini_monthly(0.00155, 2_000, 4) == pytest.approx(12.40)
    # 3 earlier turns on average in an 8-turn conversation: 1000 tokens * 3.5 * 0.25 / 1M
    assert cost_model.history_extra_per_turn(1000, 8, PRICE) == pytest.approx(0.000875)


def test_history_growth_uses_the_takamine_pair():
    rows = [row("quote", 5000, 1, 0, scenario="takamine_pix", step=0, repeat=1),
            row("quote", 5600, 1, 0, scenario="takamine_pix", step=1, repeat=1),
            row("quote", 5000, 1, 0, scenario="takamine_pix", step=0, repeat=2),
            row("quote", 5400, 1, 0, scenario="takamine_pix", step=1, repeat=2)]
    assert cost_model.history_growth_tokens(rows) == 500


def test_cloud_run_gross_and_free_tier():
    cr = {"vcpu_second_usd": 0.0000336, "gib_second_usd": 0.0000035, "requests_per_million_usd": 0.40,
          "service_shape": {"vcpu": 1, "memory_gib": 0.5},
          "free_tier_monthly": {"vcpu_seconds": 180_000, "gib_seconds": 360_000, "requests": 2_000_000,
                                "tier1_vcpu_second_usd": 0.000024, "tier1_gib_second_usd": 0.0000025}}
    c = cost_model.cloud_run_monthly(1_000, 4, 2.0, cr)
    seconds = 1_000 * (4 * 2.0 + cost_model.OVERHEAD_SECONDS_PER_CONVERSATION)
    requests = 1_000 * (4 + cost_model.REQUESTS_PER_CONVERSATION_OVERHEAD)
    gross = seconds * 0.0000336 + seconds * 0.5 * 0.0000035 + requests * 0.40 / 1e6
    discount = seconds * 0.000024 + seconds * 0.5 * 0.0000025 + requests * 0.40 / 1e6
    assert c["gross_usd"] == pytest.approx(gross)
    assert c["net_of_free_tier_usd"] == pytest.approx(gross - discount)
    # Past the free tier on CPU and memory (1.7M vCPU-s, 850k GiB-s), still inside it on requests (1.8M):
    big = cost_model.cloud_run_monthly(100_000, 8, 2.0, cr)
    capped = 180_000 * 0.000024 + 360_000 * 0.0000025 + 1_800_000 * 0.40 / 1e6
    assert big["net_of_free_tier_usd"] == pytest.approx(big["gross_usd"] - capped)


def test_report_is_built_from_the_benchmark_files(tmp_path):
    for model in cost_model.MODELS:
        rows = [row("quote", 6000, 100, 0, scenario="takamine_pix", step=0),
                row("quote", 6500, 100, 0, scenario="takamine_pix", step=1),
                row("out_of_scope", 2600, 80, 0)]
        (tmp_path / f"{cost_model.BENCHMARK_DATE}-{model}.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for r in rows))
    pricing = {"source": "s", "checked_on": "d", "unit": "u",
               "models": {m: PRICE for m in cost_model.MODELS},
               "fx": {"usd_brl": 5.0, "kind": "k", "date": "d"},
               "cloud_run": {"source": "s", "checked_on": "d", "vcpu_second_usd": 0.0000336,
                             "gib_second_usd": 0.0000035, "requests_per_million_usd": 0.40,
                             "service_shape": {"vcpu": 1, "memory_gib": 0.5},
                             "free_tier_monthly": {"vcpu_seconds": 180_000, "gib_seconds": 360_000,
                                                   "requests": 2_000_000, "tier1_vcpu_second_usd": 0.000024,
                                                   "tier1_gib_second_usd": 0.0000025}}}
    data = cost_model.build(pricing, tmp_path)
    mean = (1650 + 1775 + 770) / 3 / 1_000_000
    first = data["models"][cost_model.MODELS[0]]
    assert first["stats"]["mean_usd"] == pytest.approx(mean)
    assert first["projection"][1]["gemini_usd"] == pytest.approx(mean * 4 * 2_000)
    md = cost_model.render(data, pricing)
    assert f"US$ {mean * 4 * 2_000:,.2f}" in md
