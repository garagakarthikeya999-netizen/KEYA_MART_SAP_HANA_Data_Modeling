-- =====================================================================
-- KEYA MART - PHASE 8: ANALYTICAL VIEWS (STAR JOIN & AGGREGATIONS)
-- =====================================================================
SET SCHEMA KEYA_MART;

-- 1. Complete Star Schema Analytical Cube View (Projection + Star Join)
CREATE OR REPLACE VIEW KEYA_MART.VW_KEYA_MART_SALES_CUBE AS
SELECT
    f.order_id,
    f.order_item_id,
    f.order_status,
    d.full_date           AS order_date,
    d.year_num,
    d.quarter_num,
    d.month_num,
    d.month_name,
    d.is_weekend,
    c.customer_unique_id,
    c.customer_city,
    c.customer_state,
    p.product_id,
    p.product_category_name,
    s.seller_id,
    s.seller_city,
    s.seller_state,
    f.item_quantity,
    f.item_price,
    f.freight_value,
    f.total_item_value,
    f.delivery_days,
    f.avg_review_score
FROM KEYA_MART.FACT_SALES f
INNER JOIN KEYA_MART.DIM_DATE d     ON f.date_sk = d.date_sk
INNER JOIN KEYA_MART.DIM_CUSTOMER c ON f.customer_sk = c.customer_sk
INNER JOIN KEYA_MART.DIM_PRODUCT p  ON f.product_sk = p.product_sk
INNER JOIN KEYA_MART.DIM_SELLER s   ON f.seller_sk = s.seller_sk;

-- 2. Category Performance View (Filter: Delivered Orders + Aggregation)
CREATE OR REPLACE VIEW KEYA_MART.VW_CATEGORY_SALES_SUMMARY AS
SELECT
    product_category_name,
    COUNT(DISTINCT order_id)        AS total_orders,
    SUM(item_quantity)              AS total_items_sold,
    SUM(item_price)                 AS product_revenue,
    SUM(freight_value)              AS total_freight,
    SUM(total_item_value)           AS gross_revenue,
    ROUND(AVG(avg_review_score), 2) AS avg_review_score,
    ROUND(AVG(delivery_days), 1)    AS avg_delivery_days
FROM KEYA_MART.VW_KEYA_MART_SALES_CUBE
WHERE order_status = 'delivered'
GROUP BY product_category_name;

-- 3. Monthly & State Sales Trend View (Aggregation by Time & Geography)
CREATE OR REPLACE VIEW KEYA_MART.VW_MONTHLY_STATE_PERFORMANCE AS
SELECT
    year_num,
    month_num,
    month_name,
    customer_state,
    COUNT(DISTINCT order_id)        AS total_orders,
    SUM(item_quantity)              AS total_items_sold,
    SUM(total_item_value)           AS gross_revenue,
    ROUND(AVG(total_item_value), 2) AS avg_item_value
FROM KEYA_MART.VW_KEYA_MART_SALES_CUBE
WHERE order_status = 'delivered'
GROUP BY year_num, month_num, month_name, customer_state;