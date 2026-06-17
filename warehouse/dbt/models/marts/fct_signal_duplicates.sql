-- Embedding-based near-duplicate detection.
--
-- Within each (competitor, signal_type) group, compare signal embeddings by
-- cosine similarity (DuckDB list vector op). Pairs at/above the threshold are
-- flagged as duplicates. We keep an ordered pair (signal_id < duplicate_of) to
-- avoid mirror rows. This powers de-duplication in the dashboard/report so the
-- same announcement seen on multiple pages isn't double-counted.

{% set dup_threshold = 0.95 %}

with sigs as (
    select signal_id, competitor_id, signal_type, title, embedding
    from {{ ref('stg_signals') }}
    where embedding is not null
)

select
    a.signal_id,
    b.signal_id as duplicate_of,
    a.competitor_id,
    a.signal_type,
    a.title,
    list_cosine_similarity(a.embedding, b.embedding) as similarity
from sigs a
join sigs b
    on  a.competitor_id = b.competitor_id
    and a.signal_type = b.signal_type
    and a.signal_id < b.signal_id
where list_cosine_similarity(a.embedding, b.embedding) >= {{ dup_threshold }}
