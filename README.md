
# Mutual Fund Data Pipeline

This pipeline extracts the data from the open source api which provides details about Indian Mutual Fund Nav details.

## Setup
1. Clone the repository to the local machine
2. Configure the AWS credentials in the local machine or wherever you wish to run terraform
3. Update the terraform template with correct S3 bucket, roles and policies
3. Initialize the terraform and apply the terraform
a. `terraform plan` - To check the resources created by the terraform
b. `terraform apply` - To deploy the resources to the AWS
4. Update the correct S3 path in the Athena queries present in the `scripts.sql` table and then run the queries in Athena.

## Running the pipeline
1. To run the pipeline manually, trigger the **step-1-collect-mutual-fund-list-data**  and the subsequent lambda will be triggered automatically
2. Go to Athena and check whether the database and tables are created as per the `scripts.sql` file

## Analysis
Now we can run Analytical queries on top of the `nav_history` table

``` SQL
-- Step 1: Get the NAV 5 years ago for each scheme
WITH nav_5_years_ago AS (
    SELECT 
        scheme_code,
        nav AS nav_5_years_ago
    FROM nav_history
    WHERE nav_date = (
        SELECT MIN(nav_date)
        FROM nav_history nh2
        WHERE nh2.scheme_code = nav_history.scheme_code
          AND nav_date >= DATE_ADD('day', -5 * 365, CURRENT_DATE)
    )
),

-- Step 2: Get the latest NAV for each scheme
latest_nav AS (
    SELECT 
        scheme_code,
        nav AS latest_nav
    FROM nav_history
    WHERE nav_date = (
        SELECT MAX(nav_date)
        FROM nav_history nh2
        WHERE nh2.scheme_code = nav_history.scheme_code
    )
)

-- Step 3: Calculate returns and join with scheme names
SELECT 
    l.scheme_code,
    s.scheme_name,
    ((l.latest_nav - n.nav_5_years_ago) / n.nav_5_years_ago) * 100 AS return_percentage
FROM latest_nav l
JOIN nav_5_years_ago n
    ON l.scheme_code = n.scheme_code
JOIN schemes s
    ON l.scheme_code = s.scheme_code
ORDER BY return_percentage DESC
LIMIT 5;

```



