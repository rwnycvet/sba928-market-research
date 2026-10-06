# Retail Market Research Briefs

Reporting method: Python calculations, prepared retailer summaries and fixed report templates.

Measured findings, recommendations and limitations are identified in each brief. These application reports are evaluated separately from model-generated responses.

## Customer Purchasing Brief

**Measured finding:** 2,845 of 4,338 identified customers (65.58%) had at least two distinct qualifying purchase invoices during the recorded period.

**Limitation:** This calculation excludes purchases without CustomerIDs. It describes repeat purchasing among identified customers and is not a retention rate for all customers.

**Recommendation:** Review purchase intervals and product choices among identified repeat customers before designing a marketing test.

**Evidence source:** results/customer_purchase_summary.csv

## Inventory Brief

Measured units come from the saved product review. Inventory actions are recommendations.

| Product | Positive Units | Signed Units | Recommendation |
|---|---:|---:|---|
| 23843 — PAPER CRAFT , LITTLE BIRDIE | 80,995 | 0 | Review transaction reversals before considering replenishment; the recorded signed balance is zero or negative. |
| 23166 — MEDIUM CERAMIC TOP STORAGE JAR | 78,033 | 3,539 | Review the difference between positive and signed units, current stock and supplier lead times before setting replenishment. |
| 22197 — SMALL POPCORN HOLDER | 56,898 | 56,427 | Review the difference between positive and signed units, current stock and supplier lead times before setting replenishment. |
| 84077 — WORLD WAR 2 GLIDERS ASSTD DESIGNS | 54,951 | 53,751 | Review the difference between positive and signed units, current stock and supplier lead times before setting replenishment. |
| 85099B — JUMBO BAG RED RETROSPOT | 48,371 | 47,256 | Review the difference between positive and signed units, current stock and supplier lead times before setting replenishment. |

**Limitation:** Positive units measure sales before reversal deductions. Signed balances include negative quantities in the prepared priced records; they do not prove that every reversal has been matched to its original purchase. Stock levels, supplier lead times and demand lost through stockouts are unavailable, so exact reorder quantities cannot be determined.

**Evidence source:** results/top_five_cancellation_review.csv

## Country Sales Brief

Revenue and customer counts are measured findings. Marketing actions are recommendations.

| Country | Sales Revenue (GBP) | Identified Customers | Below-Five Warning | Marketing Recommendation |
|---|---:|---:|---|---|
| United Kingdom | 9,001,744.09 | 3,920 | No | Test a campaign based on recorded product purchases and measure incremental sales. |
| Netherlands | 285,446.34 | 9 | No | Review recorded purchase frequency and product mix to design a small marketing test. |
| EIRE | 283,140.52 | 3 | Yes | Review revenue concentration and unidentified purchases before increasing marketing spend. |

**Limitation:** Revenue represents this retailer's positive sales before return and cancellation deductions, including valid sales without CustomerIDs. The warning applies only to recorded identified-customer counts; missing IDs may represent additional customers. These records do not establish national demand or explain customer motives.

**Evidence:** results/country_revenue.csv and results/country_coverage.csv

## Monthly Sales Brief

Revenue is positive sales before return and cancellation deductions.

| Month | Revenue (GBP) | Recorded Coverage | Change (%) |
|---|---:|---|---:|
| 2010-12 | 821,452.73 | Complete month | N/A |
| 2011-01 | 689,811.61 | Complete month | -16.03 |
| 2011-02 | 522,545.56 | Complete month | -24.25 |
| 2011-03 | 716,215.26 | Complete month | +37.06 |
| 2011-04 | 536,968.49 | Complete month | -25.03 |
| 2011-05 | 769,296.61 | Complete month | +43.27 |
| 2011-06 | 760,547.01 | Complete month | -1.14 |
| 2011-07 | 718,076.12 | Complete month | -5.58 |
| 2011-08 | 757,841.38 | Complete month | +5.54 |
| 2011-09 | 1,056,435.19 | Complete month | +39.40 |
| 2011-10 | 1,151,263.73 | Complete month | +8.98 |
| 2011-11 | 1,503,866.78 | Complete month | +30.63 |
| 2011-12 | 637,790.33 | Partial month: through December 9 | N/A |

**Measured findings:**
- Largest qualifying increase: 2011-05, +43.27%.
- Largest qualifying decrease: 2011-04, -25.03%.
- Highest complete-month revenue: 2011-11, GBP 1,503,866.78.

**Recommendation:** Review inventory timing around the recorded higher-revenue months using current stock and supplier lead times.

**Limitation:** Changes are calculated only between consecutive months declared complete in the source summary. Partial-month totals cannot establish a full-month decline. These historical figures do not prove a recurring seasonal pattern or its cause.

**Evidence:** results/monthly_revenue.csv

## Competitor Research Brief

| Research Question | Evidence-Based Conclusion | Additional Data Required |
|---|---|---|
| Does this retailer outsell its competitors? | Cannot be determined from the supplied summary. | Competitor sales for matching dates, product categories and countries, using consistent currencies and treatment of returns and cancellations. |
| What is this retailer's market share? | Cannot be calculated without total-market sales. | Total-market sales covering the same period, categories, countries, sales channels and revenue definition. |
| How many retailers operate in each country? | Country sales groups do not measure retailer counts. | Dated business-register or industry data, with a consistent definition of retailer and a distinction between companies and store locations. |
| Can CustomerID counts measure competing retailers? | Customer identifiers do not establish competitor counts. | Verified competitor identities and business classifications. |

**Recommendation:** Obtain comparable competitor evidence before making competitive-positioning or market-share claims.

**Limitation:** The supplied summary describes the retailer's sales by country. It contains no competitor revenue, competitor identities or total-market sales. Missing competitor evidence must not be treated as zero competitor sales.

**Evidence:** results/country_revenue.csv
