USE [nyc-weather-jeffd];

IF OBJECT_ID('dbo.[nyc-weather-data]', 'U') IS NOT NULL
BEGIN
    PRINT 'Table [nyc-weather-data] already exists. Dropping it...';
    DROP TABLE dbo.[nyc-weather-data];
END

PRINT 'Creating table [nyc-weather-data]...';
CREATE TABLE [nyc-weather-data] (
    [date] DATE,
    [max_temp_f] INT,
    [low_temp_f] INT,
    [condition] VARCHAR(50),
    [location] VARCHAR(100)
);

PRINT 'Inserting 30 rows of data...';
INSERT INTO [nyc-weather-data] ([date], [max_temp_f], [low_temp_f], [condition], [location])
VALUES
    ('2020-02-13', 44, 34, 'sunny', 'new york city'),
    ('2020-04-20', 48, 38, 'windy', 'new york city'),
    ('2020-07-10', 44, 34, 'sunny', 'new york city'),
    ('2020-08-01', 45, 35, 'rain', 'new york city'),
    ('2020-09-12', 18, 10, 'snow', 'new york city'),
    ('2020-12-04', 18, 10, 'snow', 'new york city'),
    ('2021-06-18', 18, 10, 'sunny', 'new york city'),
    ('2021-07-09', 45, 35, 'rain', 'new york city');

PRINT 'Data insertion complete.';

PRINT 'Displaying all records from [nyc-weather-data]:';
SELECT * FROM [nyc-weather-data];