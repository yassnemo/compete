-- Hiring fact derived from job-board snapshots (source_type = 'jobs').
--
-- The jobs collector stores each posting's clean_text as "Role (Location)\n\n
-- body", so we parse role + location from the first line. posted_at is the
-- first time we observed the role; removal detection (removed_at) is left for a
-- later pass (it needs run-over-run set differencing).

with jobs as (
    select
        competitor_id,
        url,
        split_part(clean_text, chr(10), 1) as first_line,
        fetched_at
    from {{ source('raw', 'raw_pages') }}
    where source_type = 'jobs'
      and clean_text is not null
),

parsed as (
    select
        competitor_id,
        url,
        nullif(trim(regexp_replace(first_line, '\s*\(.*$', '')), '') as role,
        nullif(regexp_extract(first_line, '\(([^)]*)\)', 1), '')     as location,
        fetched_at
    from jobs
)

select
    competitor_id,
    url,
    coalesce(role, '(untitled role)') as role,
    location,
    min(fetched_at) as posted_at,
    cast(null as timestamp with time zone) as removed_at
from parsed
group by competitor_id, url, role, location
