# SBA 928 — Enhancing Market Research with AI Prompt Engineering

## Purpose
Analyze the UCI Online Retail dataset to explore purchasing patterns, product demand, and country-level sales, then use verified results to support AI prompt experiments.

## Current Progress
Implemented data inspection, positive-sales filtering, country revenue summaries, product rankings, and a cancellation review. Prompt testing, model fine-tuning, and model comparison are still pending.

## Setup
Install Git and uv. Clone this repository and open its folder in Visual Studio Code.

Run `uv sync` in the project terminal to install the recorded dependencies.

## Dataset
Source: Chen, D. (2015). Online Retail. UCI Machine Learning Repository.  
https://doi.org/10.24432/C5BW33

Download the dataset from https://archive.ics.uci.edu/dataset/352/online+retail and extract it.

Create a `data` folder in the project root and place `Online Retail.xlsx` inside it. The downloaded spreadsheet is excluded from Git.

Dataset license: Creative Commons Attribution 4.0 International (CC BY 4.0).

## Run the Analysis
From the project root, run:

`uv run python analyze_data.py`

The program prints inspection results and saves three files in `results`:

- `country_revenue.csv`
- `product_summary.csv`
- `top_five_cancellation_review.csv`

## Analysis Decisions and Limitations
Exact duplicate rows are removed as a documented assumption. Positive-sales analysis excludes cancelled invoices, nonpositive quantities, and nonpositive unit prices. Otherwise valid rows with missing CustomerIDs are retained.

Revenue represents positive sales before deductions for returns and cancellations, not profit or net revenue.

The cancellation review separately sums signed quantities from deduplicated records with positive prices. It demonstrates why high positive-sales totals alone do not justify inventory increases.

The dataset covers one retailer. Findings should not be generalized to entire countries or the retail industry.