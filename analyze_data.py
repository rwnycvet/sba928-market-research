from pathlib import Path

import pandas as pd

# Locate the dataset relative to this Python file.
project_folder = Path(__file__).resolve().parent
data_file = project_folder / "data" / "Online Retail.xlsx"

# Load the spreadsheet into a DataFrame.
df = pd.read_excel(data_file)

# Inspect the dataset before making changes.
print("Rows and columns:", df.shape)
print("\nColumn names:")
print(df.columns.tolist())

print("\nFirst five records:")
print(df.head())

print("\nMissing values by column:")
print(df.isna().sum())

# Count exact duplicate rows across all eight columns.
print("\nExact duplicate rows:")
print(df.duplicated().sum())

# Invoice numbers beginning with C identify cancellations.
cancelled = df["InvoiceNo"].astype(str).str.upper().str.startswith("C")

print("\nCancellation rows:")
print(cancelled.sum())

print("\nRows with zero or negative quantities:")
print((df["Quantity"] <= 0).sum())

print("\nRows with zero or negative unit prices:")
print((df["UnitPrice"] <= 0).sum())

# Keep one copy of each exact row.
unique_rows = df.drop_duplicates().copy()

# Recalculate the cancellation flag for this table.
is_cancelled = (
    unique_rows["InvoiceNo"]
    .astype(str)
    .str.upper()
    .str.startswith("C")
)

# Keep non-cancelled rows with positive quantities and prices.
sales = unique_rows.loc[
    (~is_cancelled)
    & (unique_rows["Quantity"] > 0)
    & (unique_rows["UnitPrice"] > 0)
].copy()

print("\nRows after removing exact duplicates:", len(unique_rows))
print("Rows retained for positive-sales analysis:", len(sales))
print("Total rows excluded:", len(df) - len(sales))
print("Retained rows missing CustomerID:", sales["CustomerID"].isna().sum())

# Calculate each retained row's sales value in British pounds.
sales["SalesRevenue"] = sales["Quantity"] * sales["UnitPrice"]

# Add the sales values for each country, then rank highest first.
country_revenue = (
    sales.groupby("Country")["SalesRevenue"]
    .sum()
    .sort_values(ascending=False)
)

print("\nTop three countries by positive sales revenue (GBP):")
print(country_revenue.head(3).round(2))

print("\nTotal positive sales revenue (GBP):")
print(round(sales["SalesRevenue"].sum(), 2))

# Group by product code so description differences do not split a product.
product_summary = (
    sales.groupby("StockCode")
    .agg(
        Description=("Description", "first"),
        UnitsSold=("Quantity", "sum")
    )
    .sort_values("UnitsSold", ascending=False)
)

# Label products that have no available description.
product_summary["Description"] = (
    product_summary["Description"].fillna("Description unavailable")
)

print("\nTop five products by units sold:")
print(product_summary.head(5).to_string())

# Inspect the purchase rows for the highest-ranked product.
top_product_code = product_summary.index[0]
top_product_sales = sales.loc[
    sales["StockCode"] == top_product_code
]

print("\nHighest-ranked product:", top_product_code)
print("Purchase rows:", len(top_product_sales))
print("Distinct purchase invoices:",
      top_product_sales["InvoiceNo"].nunique())
print("Largest single-row quantity:",
      top_product_sales["Quantity"].max())

# Check the original data for cancellations of this product.
original_cancellations = df.loc[
    (df["StockCode"] == top_product_code) & cancelled,
    ["InvoiceNo", "Quantity", "InvoiceDate"]
]

print("\nCancellation records for this product:")
print(original_cancellations.to_string(index=False))

# Compare all original records for the highest-ranked product.
print("\nOriginal records for product 23843:")
print(
    df.loc[
        df["StockCode"] == top_product_code,
        ["InvoiceNo", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID"]
    ].to_string(index=False)
)

# Compare positive-sales leaders with their signed quantity totals.
# Retain negative quantities here so cancellations affect the balance.
priced_records = unique_rows.loc[unique_rows["UnitPrice"] > 0]

signed_units = priced_records.groupby("StockCode")["Quantity"].sum()

top_five_review = product_summary.head(5).copy()
top_five_review["SignedUnitsIncludingCancellations"] = signed_units

print("\nTop five products reviewed with cancellations included:")
print(top_five_review.to_string())

# Create a results folder inside the project.
results_folder = project_folder / "results"
results_folder.mkdir(exist_ok=True)

# Save the calculated summaries.
country_revenue.to_csv(results_folder / "country_revenue.csv")
product_summary.to_csv(results_folder / "product_summary.csv")
top_five_review.to_csv(results_folder / "top_five_cancellation_review.csv")

print("\nSaved three summary files to:", results_folder)