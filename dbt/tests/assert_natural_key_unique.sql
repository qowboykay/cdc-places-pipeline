-- The combination (locationid, year, measureid, datavaluetypeid) must be unique.
-- Returns any duplicate combinations. A passing test returns 0 rows.

select
    locationid,
    year,
    measureid,
    datavaluetypeid,
    count(*) as row_count
from {{ ref('stg_places_county') }}
group by locationid, year, measureid, datavaluetypeid
having count(*) > 1
