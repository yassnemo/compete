-- Typed view of detected changes.

select
    change_id,
    competitor_id,
    url,
    signal_type,
    change_type,
    summary,
    cast(significance_score as integer) as significance_score,
    prev_hash,
    new_hash,
    detected_at
from {{ source('raw', 'changes') }}
