-- Change fact: every detected change enriched with the extracted signal's
-- title/confidence, plus a weighted significance used for ranking.
--
-- weighted_significance bumps high-impact signal types by one (capped at 5),
-- so a funding/launch/pricing/leadership move ranks above a routine update of
-- equal model-assigned significance.

with changes as (
    select * from {{ ref('stg_changes') }}
),

signals as (
    select * from {{ ref('stg_signals') }}
)

select
    c.change_id,
    c.competitor_id,
    c.url,
    c.change_type,
    coalesce(c.signal_type, s.signal_type) as signal_type,
    s.title,
    c.summary,
    coalesce(c.significance_score, s.significance) as significance_score,
    least(
        5,
        coalesce(c.significance_score, s.significance, 1)
        + case
            when coalesce(c.signal_type, s.signal_type) in (
                'funding_news', 'product_launch', 'pricing_change', 'leadership_change'
            ) then 1 else 0
        end
    ) as weighted_significance,
    s.confidence,
    s.entities,
    c.prev_hash,
    c.new_hash,
    c.detected_at
from changes c
left join signals s
    on  c.competitor_id = s.competitor_id
    and c.url = s.url
    and c.new_hash = s.source_hash
