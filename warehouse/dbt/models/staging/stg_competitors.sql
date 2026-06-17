-- Typed view of operational competitor records, with a tracked-URL count.

select
    competitor_id,
    name,
    domain,
    industry,
    cast(tier as integer) as tier,
    tracked_urls,
    coalesce(cast(json_array_length(tracked_urls) as integer), 0) as tracked_url_count,
    created_at,
    updated_at
from {{ source('raw', 'competitors') }}
