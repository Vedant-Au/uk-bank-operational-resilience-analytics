-- Descriptive public context only; no claim about fictional-bank incidents.
WITH monthly AS (
    SELECT observation_month, successful_calls, failed_calls,
           technical_failures, availability_pct, weighted_availability_pct,
           response_time_ms,
           round(100 * technical_failures / NULLIF(successful_calls + failed_calls, 0), 4)
             AS technical_failure_rate_pct,
           round(weighted_availability_pct - availability_pct, 3)
             AS weighted_unweighted_gap_pp
    FROM mart.open_banking_monthly
), changes AS (
    SELECT *,
           round(100 * (successful_calls / NULLIF(lag(successful_calls)
                 OVER (ORDER BY observation_month), 0) - 1), 2)
                 AS successful_calls_mom_pct,
           round(avg(availability_pct) OVER (
                 ORDER BY observation_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 3)
                 AS availability_3m_trailing_pct
    FROM monthly
)
SELECT observation_month, successful_calls, successful_calls_mom_pct,
       technical_failures, technical_failure_rate_pct,
       availability_pct, availability_3m_trailing_pct,
       weighted_availability_pct, weighted_unweighted_gap_pp,
       response_time_ms
FROM changes ORDER BY observation_month;

-- Inspect low availability months separately; ranking does not prove cause.
SELECT observation_month, availability_pct, weighted_availability_pct,
       technical_failures, successful_calls, failed_calls
FROM mart.open_banking_monthly
ORDER BY availability_pct, observation_month LIMIT 5;
