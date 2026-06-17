-- Lightly cleaned passthrough of the raw page snapshots.
-- The richer stg_signals model (with embeddings/significance) is built in
-- Phase 3 once extraction is in place.

select
    id,
    competitor_id,
    url,
    source_type,
    content_hash,
    clean_text,
    http_status,
    fetched_at
from {{ source('raw', 'raw_pages') }}
