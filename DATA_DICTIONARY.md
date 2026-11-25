# Data dictionary

All records are synthetic. Source IDs are numeric. Clean keys and customer-month/area-month grains are unique.

## area_service_months.csv

| Column | Type / unit | Meaning |
|---|---|---|
| service_id | integer | Unique primary key for area_service_months. |
| area_id | integer | Primary key in areas; foreign key in customers and service records. |
| month | date | Service month, first day. Snapshot raw dates may be DD/MM/YYYY; clean dates use ISO. |
| outage_hours | decimal, hours | Shared monthly area network interruption exposure; not customer-specific downtime. |
| network_incidents | integer | Scenario count of network incidents in an area-month. No incident duration detail is modeled. |

## areas.csv

| Column | Type / unit | Meaning |
|---|---|---|
| area_id | integer | Primary key in areas; foreign key in customers and service records. |
| area_name | text | Fictional service area, not a real geographic location. |
| area_type | text | Urban or Peri-urban scenario category. |

## customers.csv

| Column | Type / unit | Meaning |
|---|---|---|
| customer_id | integer | Synthetic customer primary key; foreign key in monthly snapshots. |
| area_id | integer | Primary key in areas; foreign key in customers and service records. |
| activation_month | date | First service month, ISO first-of-month YYYY-MM-DD. |
| acquisition_channel | text | Digital, Referral or Retail; remains fixed. |
| segment | text | Home, Remote worker or Microbusiness; remains fixed. |
| autopay | integer flag | 1 means automatic payment preference. Does not represent observed cash collections. |

## plans.csv

| Column | Type / unit | Meaning |
|---|---|---|
| plan_id | integer | Primary key in plans; foreign key in subscription_months. Raw invalid plan references are injected. |
| plan_name | text | Essential, Plus or Premium. |
| allowance_gb | decimal, GB/month | Included data allowance, used to cap simulated usage. |
| base_fee_ngn | decimal, NGN/month | Reference fee before 2025 increase and customer adjustments. |

## subscription_months.csv

| Column | Type / unit | Meaning |
|---|---|---|
| snapshot_id | integer | Monthly observation key; repeats only for deliberate duplicate source copies. |
| customer_id | integer | Synthetic customer primary key; foreign key in monthly snapshots. |
| plan_id | integer | Primary key in plans; foreign key in subscription_months. Raw invalid plan references are injected. |
| month | date | Service month, first day. Snapshot raw dates may be DD/MM/YYYY; clean dates use ISO. |
| tenure_month | integer, months | Zero-based months since activation; month 0 is first billed month. |
| usage_gb | decimal, GB | Monthly usage from zero up to current plan allowance; no overage model. |
| support_tickets | integer | Customer support contacts during the month; aggregates, not individual ticket records. |
| gross_fee_ngn | decimal, NGN | Full monthly plan fee including time-dependent price increase, before deductions. |
| promo_discount_ngn | decimal, NGN | 15% of fee during first three Digital-acquired months, otherwise zero. |
| service_credit_ngn | decimal, NGN | 10% of fees after promotional discount when area outage exposure exceeds eight hours. |
| end_status | text | Retained or Churned at month end. Clean lowercase; raw whitespace/case variants injected. |
| satisfaction_score | nullable integer, 1–5 | Optional customer survey. Missing is nonresponse; response probability depends on exit outcome. |

## Additional mart and quarantine fields

| Column | Type / unit | Meaning |
|---|---|---|
| churned | integer flag | 1 if end_status is churned, else 0. |
| new_customer | integer flag | 1 if tenure_month is zero. |
| net_subscription_ngn | decimal, NGN | Gross fee less promo discount and service credit; full-month service revenue assumption. |
| quality_reason | text | Why a source record or associated customer history was excluded. |

## Report fields

Counts (`exposed_customers`, `acquired_customers`, `opening_customers`, `churned_customers`, `closing_customers`, `customers`, `customer_months`, `exits`, `exposed`, `cohort_size`, `retained`) are integer counts at the grain named by each report. `gross_ngn`, `promo_ngn`, `credit_ngn`, `net_ngn` are summed NGN amounts. `arpu_ngn` is net revenue per customer-month. `mean_usage_gb` is GB per customer-month. `exposure_churn_rate`, `retention` and `allowance_utilization` are fractions, not percent values. `tickets_per_100_months` means tickets per 100 customer-months. `customer_weighted_outage` is mean monthly area outage hours weighted by the customer exposure rows. `age` is zero-based customer tenure in months. `outage_band` groups outage_hours into <4, 4–<8, 8–<16, or >=16 hours; labels 4–8 and 8–16 are abbreviated half-open intervals.

## Relationships and excluded histories
Plans to monthly subscriptions: one-to-many. Areas to customers and area_service_months: one-to-many. Customers to subscription_months: one-to-many. Join service context on customer area_id plus snapshot month. `customers` preserves the original 4,000 customers; `eligible_customers` excludes all 35 customers with an invalid snapshot. Use only eligible customers for retention analysis. Invalid rows are a subset of quarantine; quarantine includes all associated historical observations.
