# ⚡ Ontario's Energy Mix: The Accelerating Reliance on Natural Gas

An end-to-end data analysis project examining how Ontario's electricity generation mix has shifted since 2015 — with a focus on Natural Gas's evolving role as both a peaking resource and a structural baseload fallback.

This project demonstrates an end-to-end analytical workflow: automated data ingestion, SQL modelling in a containerized environment, Python-based analysis and visualization, and structured insight communication.

**Data sourced from [IESO public reports](https://reports-public.ieso.ca/public/), retrieved June 29, 2026.**

---

## Key Findings

- **Demand entered a sharp structural climb starting in 2024**, breaking years of relative stability.
- **Gas absorbed essentially all of this growth.** From Jan 2024–May 2026, total generation rose +1,138 GWh while Gas output alone rose +1,232 GWh.
- **Gas also covered most of the output lost during Ontario's Nuclear Refurbishment Program** (2020–2023), when Nuclear output fell -1,387 GWh against a total system drop of just -251 GWh.
- **Gas's share of generation rises sharply with demand stress** — from 7.8% in low-demand months, to 12.8% in high-demand months, to 15.8% in the top 10 most extreme peak months, and to as much as 18.0% in the top 5.

*Ontario's annual generation mix since 2015. Gas (red) expands to cover the Nuclear gap during the 2020–2023 refurbishment period — then keeps growing as demand climbs from 2024 onward.*

![Ontario Electricity Generation Mix Shift](img/stacked_area.png)

---

## Tech Stack

| Layer | Tool |
|---|---|
| Database | SQL Server 2022 (via Docker) |
| Schema & Queries | T-SQL — window functions, CTEs, views |
| Data Ingestion | Python (`requests`, `xml.etree.ElementTree`, `pandas`) |
| Analysis & Visualization | Python (`pandas`, `seaborn`, `plotly`) |
| Containerization | Docker + Docker Compose |

---

## Project Structure

```
├── main.ipynb                  # Full analysis notebook (start here)
├── data_ingestion.py           # Fetches and writes raw data from IESO
├── docker-compose.yml          # Spins up SQL Server and runs setup scripts
├── requirements.txt            # Python dependencies
├── csv_data/
│   ├── demand_data.csv         # Monthly demand data (total GWh + peak GW)
│   └── generation_data.csv     # Monthly generation by fuel type (GWh)
├── img/
│   ├── divergence.png          # 2020-2022 crop from Total Generation and Gas Generation chart (referenced in notebook)
│   └── stacked_area.png        # Annual fuel mix stacked area chart
└── sql_scripts/
    ├── init.sql                # Creates DB, tables, and loads CSV data
    ├── views.sql               # Creates demand views for the two analysis scopes
    ├── data_integrity.sql      # Null, duplicate, and continuity checks
    ├── demand_rolling_avg.sql          # 12-month rolling avg of demand
    ├── generation_by_fuel_rolling_avg.sql  # 12-month rolling avg by fuel output
    ├── fuel_contribution_yearly.sql    # Annual % share per fuel
    ├── top_50th_percentile.sql         # Gas share: top vs bottom 50% peak months
    ├── top_10_months.sql               # Identifies top 10 peak-demand months
    └── top_10_months_data.sql          # Gas share: top 10 vs all other months
```

---

## How to View This Project

### Tier 1 — Quick View (No Setup Required)

You do not need to install any dependencies or run any code to read this project. Simply click on `main.ipynb` above to view the complete narrative analysis and all visualizations directly in your browser on GitHub.

---

### Tier 2 — Full Technical Execution

This project features a fully automated, containerized data pipeline. You do not need to install or configure SQL Server on your local machine — Docker handles it entirely.

#### Prerequisites

- [Git](https://git-scm.com/downloads)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (with WSL 2 on Windows)
- Python 3.10+ and an IDE with Jupyter support — [Anaconda](https://www.anaconda.com/download) (includes Python + Jupyter out of the box), [VS Code](https://code.visualstudio.com/) with the [Jupyter extension](https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter), or [PyCharm](https://www.jetbrains.com/pycharm/)
- [ODBC Driver 17 or 18 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server) — required by `pyodbc` to connect the notebook to the SQL Server container. If you already have SQL Server or SSMS installed on your machine, you likely already have this and can skip it.

#### Step 1 — Clone the repository

```bash
git clone https://github.com/ksprihar/OntarioEnergyMix.git
cd OntarioEnergyMix
```

#### Step 2 — Install Python dependencies

```bash
pip install -r requirements.txt
```

#### Step 3 — (Optional) Refresh the data

The `csv_data/` folder already contains demand and generation data fetched on **June 29, 2026**. Docker will use these files by default — you can skip this step unless you want the latest data from IESO.

```bash
python data_ingestion.py
```

#### Step 4 — Start the database

This spins up a SQL Server container and automatically creates the database, tables, and views.

```bash
docker compose up
```

Wait for `Database setup successfully completed!` before closing the terminal window. First run takes ~30 seconds for SQL Server to boot.

#### Step 5 — Run the notebook

Open `main.ipynb` in your IDE or Jupyter and run all cells from top to bottom.

#### Step 6 — Shut down

```bash
docker compose down
```

---

## A Note on the Database Password

The SA password for the local SQL Server container is hardcoded in `docker-compose.yml` and `main.ipynb`. This is intentional — it's a throwaway local development database with no sensitive data, and keeping it hardcoded means setup requires zero configuration. If you'd like a different password, update it in both files.

---

## Data Sources

| Dataset | Source | Granularity |
|---|---|---|
| Generation by fuel type | [IESO — GenOutputbyFuelMonthly](https://reports-public.ieso.ca/public/GenOutputbyFuelMonthly/) | Monthly, by fuel |
| Ontario demand | [IESO — Demand](https://reports-public.ieso.ca/public/Demand/) | Hourly (aggregated to monthly) |

---

## Scope and Limitations

- **Monthly resolution only.** The peak demand analysis uses the single highest hourly reading per month, not full hourly data. A true hour-by-hour dispatch analysis would require building a generator-to-fuel mapping table — a deliberate out-of-scope decision for this project.
- **Generation data only covers grid-connected sources.** Distributed rooftop solar is excluded from the IESO generation reports.
- **Top 5 peak months caveat.** Three of the five highest peak-demand months on record fall within summer 2025, so the Top 5 result may partly reflect one unusually hot season. The Top 10 and 50th-percentile splits draw from a wider range of years and are the more robust evidence.
- **September anomaly.** Septembers 2016, 2018, and 2023 appear in the Top 10 peak months despite September having lower total monthly demand than July or August. This is a consistent, structural pattern across all three years — not a data error — but the root cause would require hourly-level investigation.
