-- Age-adjusted prevalence for all measures, with county context joined in.
-- Filtering to AgeAdjPrv removes the crude/adjusted duplication,
-- reducing 229k rows to ~115k (one row per county per year per measure).

with age_adjusted as (
    select *
    from {{ ref('stg_places_county') }}
    where datavaluetypeid = 'AgeAdjPrv'
),

-- Derive a county dimension by taking the max population figures per county.
-- Max is safe here because population is the same across all measure rows
-- for a given county; max just picks a non-null value if any rows differ.
county_dim as (
    select distinct
        locationid,
        locationname,
        stateabbr,
        statedesc,
        max(totalpopulation) as totalpopulation,
        max(totalpop18plus)  as totalpop18plus
    from {{ ref('stg_places_county') }}
    group by locationid, locationname, stateabbr, statedesc
)

select
    a.year,
    d.locationid,
    d.locationname,
    d.stateabbr,
    d.statedesc,
    d.totalpopulation,
    d.totalpop18plus,
    a.category,
    a.categoryid,
    a.measure,
    a.measureid,
    a.short_question_text,
    a.data_value,
    a.low_confidence_limit,
    a.high_confidence_limit,
    a.data_value_footnote_symbol,
    a.data_value_footnote
from age_adjusted a
inner join county_dim d on a.locationid = d.locationid
