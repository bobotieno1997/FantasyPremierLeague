# Fanstasy Premier League

![Description of the image](https://github.com/bobotieno1997/FPL/blob/9b4eddd462aee2402433df7c01296e20d24cbda3/Others/FPL-Statement-Lead.webp)

This repository contains the SQL and Python code for managing the Fantasy Premier League (FPL) dataset. Data is accessed via RESTful API endpoints provided by FPL and ingested using Python scripts. During ingestion, little transformations are done before loading the data to postgres instance hosted on Aiven.

---
## The Architecture
The Solution approach selected based on how the data is made available was the medalion architecture
![Description of the image](https://github.com/bobotieno1997/FantasyPremierLeague/blob/26ecda6d5dcc48fffb1f4318bf02c65a142dd4df/project_files/Architecture/overview_architecture%20.jpg)

This is the preferred approach since data is only available for the current season through the API. Data is ingested from the API and loaded to the bronze layer. The main idea is for the data to be available for processing before loading the it to the silver layer. Silver layer is handled differently compared to the bronze layer in that bronze layer truncates and loads in all DAG runs while the silver layer only gets updated if any record in the silver layer needs to, this ensures history data is saved. The gold layer is primarily views reading data directly from the silver layer. The gold layer uses a snowflake schema due to the nature of the data.

The processed data in the data warehouse layer is optimized for analytical workloads and data visualization, enabling insightful exploration and reporting for FPL enthusiasts and analysts.

## Technologies Used:
- Postgres Database
- Python Programming 
- Docker
- Apache Airflow

## 📂 Repository Structure (Key Documents)
```
├───config
├───dags
│   ├───00_Initialization --Database and Schema creation scripts
│   ├───01_Bronze
│   │   ├───Scripts       -- Scripts to load data to bronze layer
│   ├───02_Silver
│   │   ├───Scripts
│   │   │   ├───01_teams    -- Store Procedure to update teams silver layer table
│   │   │   ├───02_players  -- Store Procedure to update player silver layer table
│   │   │   ├───03_games    -- Store Procedure to update games silver layer table
│   │   │   └───04_stats   -- Store Procedure to update stats silver layer table
│   │   └───__pycache__
│   └───03_Gold            -- Scripts to create gold layer views
├───logs
├───plugins
└───project_files
    ├───Architecture      -- Architecture Images and dat flow
    └───Documentation     -- naming convension and project takeways

```
