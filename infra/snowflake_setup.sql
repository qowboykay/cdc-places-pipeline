-- ============================================================
-- CDC PLACES Snowflake Setup
-- Run as ACCOUNTADMIN in a Snowflake Worksheet.
-- Execute Part 1 first, then follow the AWS steps before Part 2.
-- ============================================================

-- ============================================================
-- PART 1: Database, warehouse, schemas, role, grants
-- ============================================================

USE ROLE ACCOUNTADMIN;

-- Virtual warehouse (XS, auto-suspends after 60s idle to save credits)
CREATE WAREHOUSE IF NOT EXISTS CDC_PLACES_WH
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND   = 60
    AUTO_RESUME    = TRUE
    COMMENT        = 'Warehouse for CDC PLACES pipeline and dbt';

-- Database
CREATE DATABASE IF NOT EXISTS CDC_PLACES
    COMMENT = 'CDC PLACES public health data';

-- Schemas (mirror dbt layer names)
CREATE SCHEMA IF NOT EXISTS CDC_PLACES.RAW;
CREATE SCHEMA IF NOT EXISTS CDC_PLACES.MAIN_STAGING;
CREATE SCHEMA IF NOT EXISTS CDC_PLACES.MAIN_INTERMEDIATE;
CREATE SCHEMA IF NOT EXISTS CDC_PLACES.MAIN_MARTS;

-- Role used by dbt and the pipeline
CREATE ROLE IF NOT EXISTS DBT_ROLE;

-- Warehouse access
GRANT USAGE ON WAREHOUSE CDC_PLACES_WH TO ROLE DBT_ROLE;

-- Database access
GRANT USAGE ON DATABASE CDC_PLACES TO ROLE DBT_ROLE;

-- Schema-level grants
GRANT USAGE, CREATE TABLE, CREATE VIEW, CREATE STAGE
    ON SCHEMA CDC_PLACES.RAW               TO ROLE DBT_ROLE;
GRANT USAGE, CREATE TABLE, CREATE VIEW
    ON SCHEMA CDC_PLACES.MAIN_STAGING      TO ROLE DBT_ROLE;
GRANT USAGE, CREATE TABLE, CREATE VIEW
    ON SCHEMA CDC_PLACES.MAIN_INTERMEDIATE TO ROLE DBT_ROLE;
GRANT USAGE, CREATE TABLE, CREATE VIEW
    ON SCHEMA CDC_PLACES.MAIN_MARTS        TO ROLE DBT_ROLE;

-- Attach role to your user
GRANT ROLE DBT_ROLE TO USER QOWBOYKAY;

-- Set a password for programmatic access (replace the placeholder)
ALTER USER QOWBOYKAY SET PASSWORD = 'ReplaceMe123!';

-- Raw table (all VARCHAR; casting happens in the dbt staging layer)
CREATE TABLE IF NOT EXISTS CDC_PLACES.RAW.PLACES_COUNTY (
    year                       VARCHAR,
    stateabbr                  VARCHAR,
    statedesc                  VARCHAR,
    locationname               VARCHAR,
    locationid                 VARCHAR,
    datasource                 VARCHAR,
    category                   VARCHAR,
    categoryid                 VARCHAR,
    measure                    VARCHAR,
    measureid                  VARCHAR,
    short_question_text        VARCHAR,
    data_value_type            VARCHAR,
    datavaluetypeid            VARCHAR,
    data_value_unit            VARCHAR,
    data_value                 VARCHAR,
    low_confidence_limit       VARCHAR,
    high_confidence_limit      VARCHAR,
    totalpopulation            VARCHAR,
    totalpop18plus             VARCHAR,
    data_value_footnote_symbol VARCHAR,
    data_value_footnote        VARCHAR,
    _loaded_at                 TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

GRANT SELECT, INSERT, TRUNCATE ON TABLE CDC_PLACES.RAW.PLACES_COUNTY TO ROLE DBT_ROLE;

-- ============================================================
-- PART 2: S3 storage integration and stage
-- Run AFTER completing the AWS IAM role steps (see README).
-- ============================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE CDC_PLACES;
USE SCHEMA RAW;

-- Storage integration (replace the role ARN after creating it in AWS)
CREATE STORAGE INTEGRATION IF NOT EXISTS s3_cdc_places
    TYPE                      = EXTERNAL_STAGE
    STORAGE_PROVIDER          = 'S3'
    ENABLED                   = TRUE
    STORAGE_AWS_ROLE_ARN      = 'arn:aws:iam::292914686819:role/snowflake-s3-cdc-places'
    STORAGE_ALLOWED_LOCATIONS = ('s3://cdc-places-qowboykay/raw/');

-- After creating the integration, run DESC to get the values needed for the AWS trust policy.
-- STORAGE_AWS_IAM_USER_ARN : arn:aws:iam::085351677760:user/2oes1000-s
-- STORAGE_AWS_EXTERNAL_ID  : BP79744_SFCRole=4_FBNY+KQrfcnyopAaGBZEfcv1V5Y=
DESC INTEGRATION s3_cdc_places;

-- Create the external stage (run after updating the IAM trust policy)
CREATE STAGE IF NOT EXISTS CDC_PLACES.RAW.s3_raw
    STORAGE_INTEGRATION = s3_cdc_places
    URL                 = 's3://cdc-places-qowboykay/raw/'
    FILE_FORMAT         = (TYPE = 'JSON' STRIP_OUTER_ARRAY = TRUE);

GRANT READ ON STAGE CDC_PLACES.RAW.s3_raw TO ROLE DBT_ROLE;
