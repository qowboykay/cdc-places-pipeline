-- Wide county health table: one row per county per year.
-- Age-adjusted prevalence for all 40 PLACES measures as individual columns,
-- grouped by category. Suitable for cross-measure comparisons, choropleth maps,
-- and scatter plots in the Streamlit dashboard.

select
    year,
    locationid,
    locationname,
    stateabbr,
    statedesc,
    totalpopulation,
    totalpop18plus,

    -- Disability
    max(case when measureid = 'DISABILITY'    then data_value end) as disability_pct,
    max(case when measureid = 'COGNITION'     then data_value end) as cognitive_disability_pct,
    max(case when measureid = 'HEARING'       then data_value end) as hearing_disability_pct,
    max(case when measureid = 'INDEPLIVE'     then data_value end) as independent_living_disability_pct,
    max(case when measureid = 'MOBILITY'      then data_value end) as mobility_disability_pct,
    max(case when measureid = 'SELFCARE'      then data_value end) as selfcare_disability_pct,
    max(case when measureid = 'VISION'        then data_value end) as vision_disability_pct,

    -- Health Outcomes
    max(case when measureid = 'ARTHRITIS'     then data_value end) as arthritis_pct,
    max(case when measureid = 'BPHIGH'        then data_value end) as high_blood_pressure_pct,
    max(case when measureid = 'CANCER'        then data_value end) as cancer_pct,
    max(case when measureid = 'CASTHMA'       then data_value end) as asthma_pct,
    max(case when measureid = 'CHD'           then data_value end) as coronary_heart_disease_pct,
    max(case when measureid = 'COPD'          then data_value end) as copd_pct,
    max(case when measureid = 'DEPRESSION'    then data_value end) as depression_pct,
    max(case when measureid = 'DIABETES'      then data_value end) as diabetes_pct,
    max(case when measureid = 'HIGHCHOL'      then data_value end) as high_cholesterol_pct,
    max(case when measureid = 'OBESITY'       then data_value end) as obesity_pct,
    max(case when measureid = 'STROKE'        then data_value end) as stroke_pct,
    max(case when measureid = 'TEETHLOST'     then data_value end) as all_teeth_lost_pct,

    -- Health Risk Behaviors
    max(case when measureid = 'BINGE'         then data_value end) as binge_drinking_pct,
    max(case when measureid = 'CSMOKING'      then data_value end) as current_smoking_pct,
    max(case when measureid = 'LPA'           then data_value end) as physical_inactivity_pct,
    max(case when measureid = 'SLEEP'         then data_value end) as short_sleep_pct,

    -- Health Status
    max(case when measureid = 'GHLTH'         then data_value end) as poor_general_health_pct,
    max(case when measureid = 'MHLTH'         then data_value end) as frequent_mental_distress_pct,
    max(case when measureid = 'PHLTH'         then data_value end) as frequent_physical_distress_pct,

    -- Health-Related Social Needs
    max(case when measureid = 'EMOTIONSPT'    then data_value end) as lack_social_support_pct,
    max(case when measureid = 'FOODINSECU'    then data_value end) as food_insecurity_pct,
    max(case when measureid = 'FOODSTAMP'     then data_value end) as food_stamps_pct,
    max(case when measureid = 'HOUSINSECU'    then data_value end) as housing_insecurity_pct,
    max(case when measureid = 'LACKTRPT'      then data_value end) as transportation_barriers_pct,
    max(case when measureid = 'LONELINESS'    then data_value end) as loneliness_pct,
    max(case when measureid = 'SHUTUTILITY'   then data_value end) as utility_threat_pct,

    -- Prevention
    max(case when measureid = 'ACCESS2'       then data_value end) as uninsured_pct,
    max(case when measureid = 'BPMED'         then data_value end) as bp_medication_pct,
    max(case when measureid = 'CHECKUP'       then data_value end) as annual_checkup_pct,
    max(case when measureid = 'CHOLSCREEN'    then data_value end) as cholesterol_screening_pct,
    max(case when measureid = 'COLON_SCREEN'  then data_value end) as colorectal_screening_pct,
    max(case when measureid = 'DENTAL'        then data_value end) as dental_visit_pct,
    max(case when measureid = 'MAMMOUSE'      then data_value end) as mammography_pct

from {{ ref('int_places_measures') }}
group by year, locationid, locationname, stateabbr, statedesc, totalpopulation, totalpop18plus
order by stateabbr, locationname
