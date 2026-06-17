-- Weekly rollup per competitor — feeds the dashboard trend cards and the
-- weekly report generator.

with changes as (
    select * from {{ ref('fct_changes') }}
)

select
    competitor_id,
    cast(date_trunc('week', detected_at) as date) as week,
    count(*)                                          as total_changes,
    count(*) filter (where weighted_significance >= 4) as high_significance_changes,
    count(*) filter (where change_type = 'new')        as new_changes,
    count(*) filter (where change_type = 'updated')    as updated_changes,
    count(distinct signal_type)                        as distinct_signal_types,
    round(avg(significance_score), 2)                  as avg_significance,
    max(weighted_significance)                         as top_significance,
    max(detected_at)                                   as last_change_at
from changes
group by competitor_id, week
