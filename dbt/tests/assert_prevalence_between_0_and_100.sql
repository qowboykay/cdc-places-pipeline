-- All PLACES measures are percentages and must fall within [0, 100].
-- Returns rows where a non-null data_value violates this constraint.
-- A passing test returns 0 rows.

select *
from {{ ref('stg_places_county') }}
where data_value is not null
  and (data_value < 0 or data_value > 100)
