-- Competitor dimension enriched with signal activity rollups.

with competitors as (
    select * from {{ ref('stg_competitors') }}
),

signal_rollup as (
    select
        competitor_id,
        count(*)                                   as signal_count,
        count(*) filter (where significance >= 4)  as high_significance_count,
        max(extracted_at)                          as last_signal_at
    from {{ ref('stg_signals') }}
    group by 1
)

select
    c.competitor_id,
    c.name,
    c.domain,
    c.industry,
    c.tier,
    c.tracked_urls,
    c.tracked_url_count,
    coalesce(r.signal_count, 0)            as signal_count,
    coalesce(r.high_significance_count, 0) as high_significance_count,
    r.last_signal_at
from competitors c
left join signal_rollup r using (competitor_id)
