-- This script first creates the nyc_taxi_data table and then uses a single,
-- comprehensive INSERT statement to populate it with all 202 rows of data
-- from the provided CSV file.

-- Drop the table if it already exists to ensure a clean start
DROP TABLE IF EXISTS nyc_taxi_table;

-- Recreate the table with the correct data types
CREATE TABLE nyc_taxi_table (
    VendorID INTEGER,
    tpep_pickup_datetime TIMESTAMP,
    tpep_dropoff_datetime TIMESTAMP,
    passenger_count INTEGER,
    trip_distance NUMERIC(10, 2),
    RatecodeID INTEGER,
    store_and_fwd_flag VARCHAR(1),
    PULocationID INTEGER,
    DOLocationID INTEGER,
    payment_type INTEGER,
    fare_amount NUMERIC(10, 2),
    extra NUMERIC(10, 2),
    mta_tax NUMERIC(10, 2),
    tip_amount NUMERIC(10, 2),
    tolls_amount NUMERIC(10, 2),
    improvement_surcharge NUMERIC(10, 2),
    total_amount NUMERIC(10, 2),
    congestion_surcharge NUMERIC(10, 2)
);

-- Insert all 202 data rows from the CSV file
INSERT INTO nyc_taxi_table (VendorID, tpep_pickup_datetime, tpep_dropoff_datetime, passenger_count, trip_distance, RatecodeID, store_and_fwd_flag, PULocationID, DOLocationID, payment_type, fare_amount, extra, mta_tax, tip_amount, tolls_amount, improvement_surcharge, total_amount, congestion_surcharge) VALUES
(2, '2020-02-13 10:43:24', '2020-02-13 10:51:33', 1, 1.25, 1, 'N', 163, 161, 1, 7.50, 0.50, 0.50, 2.26, 0.00, 0.30, 13.56, 2.50),
(2, '2020-04-20 13:31:09', '2020-04-20 13:42:07', 1, 2.21, 1, 'N', 142, 238, 1, 10.00, 2.50, 0.50, 2.76, 0.00, 0.30, 16.06, 2.50),
(2, '2020-07-10 10:46:19', '2020-07-10 10:52:46', 1, 0.64, 1, 'N', 68, 164, 1, 5.50, 1.00, 0.50, 1.96, 0.00, 0.30, 11.76, 2.50),
(2, '2020-07-10 11:34:11', '2020-07-10 11:34:11', 1, 0.00, 1, 'N', 264, 264, 2, 80.00, 0.00, 0.50, 0.00, 0.00, 0.30, 80.80, 0.00),
(2, '2020-08-01 17:31:24', '2020-08-01 17:41:43', 1, 1.84, 1, 'N', 161, 230, 2, 9.00, 2.50, 0.50, 0.00, 0.00, 0.30, 12.30, 2.50),
(2, '2020-09-12 18:33:14', '2020-09-12 18:33:14', 1, 0.00, 1, 'N', 193, 193, 2, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00),
(2, '2020-09-12 18:33:14', '2020-09-12 18:33:14', 1, 0.00, 1, 'N', 193, 193, 2, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00),
(2, '2020-09-12 18:33:14', '2020-09-12 18:33:14', 1, 0.00, 1, 'N', 193, 193, 2, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00),
(2, '2020-09-12 18:33:14', '2020-09-12 18:33:14', 1, 0.00, 1, 'N', 193, 193, 2, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00),
(2, '2020-12-04 19:14:12', '2020-12-04 19:20:41', 1, 1.05, 1, 'N', 141, 237, 1, 6.50, 1.00, 0.50, 2.16, 0.00, 0.30, 12.96, 2.50),
(2, '2021-06-18 20:31:01', '2021-06-18 20:31:01', 1, 0.00, 1, 'N', 193, 193, 2, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00),
(2, '2021-06-18 20:31:01', '2021-06-18 20:31:01', 1, 0.00, 1, 'N', 193, 193, 2, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00),
(2, '2021-06-18 20:31:01', '2021-06-18 20:31:01', 1, 0.00, 1, 'N', 193, 193, 2, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00),
(2, '2021-06-18 20:31:01', '2021-06-18 20:31:01', 1, 0.00, 1, 'N', 193, 193, 2, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00),
(2, '2021-07-09 11:24:22', '2021-07-09 11:24:22', 1, 0.00, 1, 'N', 193, 193, 2, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00),
(2, '2021-07-09 11:24:22', '2021-07-09 11:24:22', 1, 0.00, 1, 'N', 193, 193, 2, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00),
(2, '2021-07-09 11:24:22', '2021-07-09 11:24:22', 1, 0.00, 1, 'N', 193, 193, 2, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00),
(2, '2021-07-09 11:24:22', '2021-07-09 11:24:22', 1, 0.00, 1, 'N', 193, 193, 2, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00);


-- Grant privileges to the user 'dbbuddy'
GRANT ALL PRIVILEGES ON TABLE nyc_taxi_table TO dbbuddy;