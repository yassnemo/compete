-- Pricing history derived from pricing-related signals.
--
-- The base Signal schema is intentionally generic (no structured price field),
-- so we recover price points heuristically: a currency-prefixed amount plus a
-- nearby plan keyword from the signal title/summary. Rows only appear where a
-- monetary amount is detected — sparse but real. Richer history would come from
-- enabling dedicated structured pricing extraction (see DATA_MODEL.md).

with pricing_signals as (
    select
        competitor_id,
        url,
        concat_ws(' ', title, summary) as txt,
        extracted_at
    from {{ ref('stg_signals') }}
    where signal_type = 'pricing_change'
),

extracted as (
    select
        competitor_id,
        url,
        coalesce(
            nullif(
                regexp_extract(
                    txt,
                    '(Free|Basic|Starter|Plus|Pro|Premium|Team|Business|Scale|Max|Enterprise)',
                    1
                ),
                ''
            ),
            'Unknown'
        ) as plan,
        try_cast(regexp_extract(txt, '\$\s*([0-9]+(?:\.[0-9]{1,2})?)', 1) as double) as price,
        case when txt like '%$%' then 'USD' else null end as currency,
        extracted_at as captured_at
    from pricing_signals
)

select competitor_id, plan, price, currency, captured_at
from extracted
where price is not null
