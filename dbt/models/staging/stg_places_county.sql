with source as (
    select * from {{ source('raw', 'places_county') }}
)

select
    cast(year as integer)                           as year,
    stateabbr,
    statedesc,
    locationname,
    locationid,
    datasource,
    category,
    categoryid,
    measure,
    measureid,
    short_question_text,
    data_value_type,
    datavaluetypeid,
    data_value_unit,
    try_cast(data_value as double)                  as data_value,
    try_cast(low_confidence_limit as double)        as low_confidence_limit,
    try_cast(high_confidence_limit as double)       as high_confidence_limit,
    try_cast(totalpopulation as integer)            as totalpopulation,
    try_cast(totalpop18plus as integer)             as totalpop18plus,
    data_value_footnote_symbol,
    data_value_footnote
    -- geolocation (complex struct) and Socrata computed region columns dropped here
from source
-- Exclude the CDC national summary row (locationid='59', stateabbr='US').
-- This dataset is county-level only; the summary row has no locationname.
where stateabbr != 'US'
