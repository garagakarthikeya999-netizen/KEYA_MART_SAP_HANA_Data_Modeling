-- =====================================================================
-- KEYA MART - PHASE 9: TESTING, RECONCILIATION & MEMORY ANALYSIS
-- =====================================================================

-- TEST 1: Revenue & Row Count Reconciliation (OLTP vs Star Schema)
SELECT
    (SELECT COUNT(*) FROM KEYA_MART.ORDER_ITEMS)           AS olp_item_rows,
    (SELECT COUNT(*) FROM KEYA_MART.FACT_SALES)            AS star_fact_rows,
    (SELECT SUM(price) FROM KEYA_MART.ORDER_ITEMS)         AS olp_total_price,
    (SELECT SUM(item_price) FROM KEYA_MART.FACT_SALES)     AS star_total_price
FROM DUMMY;

-- TEST 2: Top 5 Product Categories (Delivered Orders)
SELECT TOP 5
    product_category_name,
    total_orders,
    total_items_sold,
    gross_revenue,
    avg_review_score
FROM KEYA_MART.VW_CATEGORY_SALES_SUMMARY
ORDER BY gross_revenue DESC;

-- TEST 3: Top 5 Customer States by Gross Revenue
SELECT TOP 5
    customer_state,
    SUM(total_orders)     AS total_orders,
    SUM(total_items_sold) AS total_items_sold,
    SUM(gross_revenue)    AS gross_revenue
FROM KEYA_MART.VW_MONTHLY_STATE_PERFORMANCE
GROUP BY customer_state
ORDER BY gross_revenue DESC;

-- TEST 4: SAP HANA Column-Store In-Memory Footprint
SELECT
    TABLE_NAME,
    RECORD_COUNT,
    ROUND(MEMORY_SIZE_IN_TOTAL / 1048576, 2) AS TOTAL_MEMORY_MB
FROM SYS.M_CS_TABLES
WHERE SCHEMA_NAME = 'KEYA_MART'
ORDER BY MEMORY_SIZE_IN_TOTAL DESC;