-- Cleaned, typed view of the LLM-extracted signals.
-- The embedding (FLOAT[]) is carried through for the dedup model.

select
    id                       as signal_id,
    competitor_id,
    url,
    signal_type,
    title,
    summary,
    entities,                -- JSON array of strings
    cast(significance as integer) as significance,
    cast(confidence as double)    as confidence,
    embedding,
    source_hash,
    model,
    extracted_at
from {{ source('raw', 'signals') }}
