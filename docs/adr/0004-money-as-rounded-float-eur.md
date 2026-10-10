# ADR-0004: Money is a float in EUR, rounded at output

**Status:** accepted, 2026-10-10

## Decision
All money is `float` EUR. Calculate at full precision. Round to 2 dp only when building output models. Fractions (rates, shares) are rounded to 4 dp and `emergency_fund_months` to 2 dp. Tests compare with `pytest.approx(expected, abs=0.01)`. Transaction amounts are signed: negative is money out.

## Consequences
This works directly with Pandas. Cent-level drift can't build up because nothing is rounded mid-calculation.
