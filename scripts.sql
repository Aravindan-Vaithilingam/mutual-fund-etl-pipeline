CREATE DATABASE IF NOT EXISTS mutual_fund_db
COMMENT 'This is your indian mutual fund db'
LOCATION 's3://aravindan-dev-space/athena-metadata/';


CREATE EXTERNAL TABLE IF NOT EXISTS schemes (
    scheme_code INT,
    scheme_name STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
WITH SERDEPROPERTIES (
  'field.delim' = ',',
  'escape.delim' = '\\',
  'line.delim' = '\n'
)
LOCATION 's3://aravindan-dev-space/mutual-fund-data-pipeline/scheme_list_data/'
TBLPROPERTIES ("skip.header.line.count" = "1");




--CREATE EXTERNAL TABLE IF NOT EXISTS schemes (
--    scheme_code INT,
--    scheme_name STRING
--)
--ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
--WITH SERDEPROPERTIES (
--  'field.delim' = ',',
--  'escape.delim' = '\\',
--  'line.delim' = '\n'
--)
--STORED AS INPUTFORMAT 'org.apache.hadoop.mapred.TextInputFormat'
--OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
--LOCATION 's3://aravindan-dev-space/mutual-fund-data-pipeline/scheme_list_data/'
--TBLPROPERTIES (
--  "skip.header.line.count" = "1",
--  "compressionType" = "GZIP"
--);



CREATE EXTERNAL TABLE IF NOT EXISTS historical_data_status (
    scheme_code INT,
    crawled_historical_data BOOLEAN
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
WITH SERDEPROPERTIES (
  'field.delim' = ',',
  'escape.delim' = '\\',
  'line.delim' = '\n'
)
LOCATION 's3://aravindan-dev-space/mutual-fund-data-pipeline/historical_data_status/'
TBLPROPERTIES ("skip.header.line.count" = "1");

CREATE EXTERNAL TABLE IF NOT EXISTS nav_history(
    scheme_code INT,
    nav_date DATE,
    nav FLOAT
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
WITH SERDEPROPERTIES (
  'field.delim' = ',',
  'escape.delim' = '\\',
  'line.delim' = '\n'
)
LOCATION 's3://aravindan-dev-space/mutual-fund-data-pipeline/mutual-fund-nav-history/'
TBLPROPERTIES ("skip.header.line.count" = "1");


CREATE TABLE IF NOT EXISTS historical_data_status (
    scheme_code INT,
    crawled_historical_data BOOLEAN
)
PARTITIONED BY (scheme_code)
LOCATION 's3://aravindan-dev-space/mutual-fund-data-pipeline/historical_data_status/'
TBLPROPERTIES (
    'table_type' = 'ICEBERG',
    'format' = 'parquet',
  'write_compression'='snappy',
  'optimize_rewrite_delete_file_threshold'='10'
);


CREATE EXTERNAL TABLE IF NOT EXISTS scheme_metadata(
        fund_house STRING,
        scheme_type STRING,
        scheme_category STRING,
        scheme_code INT,
        scheme_name STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
WITH SERDEPROPERTIES (
  'field.delim' = ',',
  'escape.delim' = '\\',
  'line.delim' = '\n'
)
LOCATION 's3://aravindan-dev-space/mutual-fund-data-pipeline/mutual-fund-meta-data/'
TBLPROPERTIES ("skip.header.line.count" = "1");

