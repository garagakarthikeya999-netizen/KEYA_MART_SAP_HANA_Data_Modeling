@'
-- =====================================================================
-- KEYA MART - WEEK 3: BASELINE ANALYTICAL BENCHMARK QUERIES (Q01 - Q10)
-- =====================================================================

-- [Q01] Total Sales Revenue (Delivered Orders)
SELECT
    COUNT(DISTINCT order_id)        AS total_orders,
    SUM(item_quantity)              AS total_items_sold,
    SUM(item_price)                 AS product_revenue,
    SUM(freight_value)              AS total_freight,
    SUM(total_item_value)           AS gross_revenue,
    ROUND(AVG(total_item_value), 2) AS avg_item_value
FROM KEYA_MART.FACT_SALES
WHERE order_status = 'delivered';

-- [Q02] Monthly Revenue Analysis (via Full Sales Cube View)
SELECT
    year_num,
    month_num,
    month_name,
    COUNT(DISTINCT order_id)        AS total_orders,
    SUM(item_quantity)              AS total_items_sold,
    SUM(total_item_value)           AS gross_revenue,
    ROUND(AVG(total_item_value), 2) AS avg_item_value
FROM KEYA_MART.VW_KEYA_MART_SALES_CUBE
WHERE order_status = 'delivered'
GROUP BY year_num, month_num, month_name
ORDER BY year_num, month_num;

-- [Q03] Top-Selling Product Categories (Top 10)
SELECT TOP 10
    product_category_name,
    total_orders,
    total_items_sold,
    product_revenue,
    gross_revenue,
    avg_review_score,
    avg_delivery_days
FROM KEYA_MART.VW_CATEGORY_SALES_SUMMARY
ORDER BY gross_revenue DESC;

-- [Q04] Top-Performing Sellers (Top 10)
SELECT TOP 10
    s.seller_id,
    s.seller_city,
    s.seller_state,
    COUNT(DISTINCT f.order_id)        AS total_orders,
    SUM(f.item_quantity)              AS total_items_sold,
    SUM(f.total_item_value)           AS gross_revenue,
    ROUND(AVG(f.avg_review_score), 2) AS avg_review_score
FROM KEYA_MART.FACT_SALES f
INNER JOIN KEYA_MART.DIM_SELLER s ON f.seller_sk = s.seller_sk
WHERE f.order_status = 'delivered'
GROUP BY s.seller_id, s.seller_city, s.seller_state
ORDER BY gross_revenue DESC;

-- [Q05] Customer Purchase Analysis (Top 20 Repeat Customers)
SELECT TOP 20
    c.customer_unique_id,
    c.customer_state,
    COUNT(DISTINCT f.order_id)        AS total_orders,
    SUM(f.item_quantity)              AS total_items_bought,
    SUM(f.total_item_value)           AS total_spend,
    ROUND(AVG(f.total_item_value), 2) AS avg_item_spend
FROM KEYA_MART.FACT_SALES f
INNER JOIN KEYA_MART.DIM_CUSTOMER c ON f.customer_sk = c.customer_sk
WHERE f.order_status = 'delivered'
GROUP BY c.customer_unique_id, c.customer_state
HAVING COUNT(DISTINCT f.order_id) > 1
ORDER BY total_spend DESC;

-- [Q06] State-Wise Sales Analysis
SELECT
    customer_state,
    SUM(total_orders)     AS total_orders,
    SUM(total_items_sold) AS total_items_sold,
    SUM(gross_revenue)    AS gross_revenue
FROM KEYA_MART.VW_MONTHLY_STATE_PERFORMANCE
GROUP BY customer_state
ORDER BY gross_revenue DESC;

-- [Q07] Order Status Analysis
SELECT
    order_status,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(item_quantity)       AS total_items,
    SUM(total_item_value)    AS total_value,
    ROUND(
        COUNT(DISTINCT order_id) * 100.0 /
        SUM(COUNT(DISTINCT order_id)) OVER (),
        2
    ) AS order_share_pct
FROM KEYA_MART.FACT_SALES
GROUP BY order_status
ORDER BY total_orders DESC;

-- [Q08] Average Delivery Time vs. Estimated Delivery by State
SELECT
    c.customer_state,
    COUNT(*) AS delivered_orders,
    ROUND(AVG(DAYS_BETWEEN(o.order_purchase_timestamp, o.order_delivered_customer_date)), 2) AS avg_actual_delivery_days,
    ROUND(AVG(DAYS_BETWEEN(o.order_purchase_timestamp, o.order_estimated_delivery_date)), 2) AS avg_estimated_delivery_days,
    SUM(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END) AS late_orders
FROM KEYA_MART.ORDERS o
INNER JOIN KEYA_MART.CUSTOMERS c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
GROUP BY c.customer_state
ORDER BY avg_actual_delivery_days DESC;

-- [Q09] Payment Type Analysis
SELECT
    p.payment_type,
    COUNT(*)                              AS payment_transactions,
    COUNT(DISTINCT p.order_id)            AS unique_orders,
    SUM(p.payment_value)                  AS total_payment_value,
    ROUND(AVG(p.payment_value), 2)        AS avg_payment_value,
    ROUND(AVG(p.payment_installments), 2) AS avg_installments
FROM KEYA_MART.PAYMENTS p
INNER JOIN KEYA_MART.ORDERS o ON p.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY p.payment_type
ORDER BY total_payment_value DESC;

-- [Q10] Complex Multi-Table OLTP Join (State x Category Top 20)
SELECT TOP 20
    c.customer_state,
    COALESCE(p.product_category_name, 'unknown') AS product_category_name,
    COUNT(DISTINCT o.order_id)                   AS total_orders,
    COUNT(*)                                     AS total_items,
    SUM(oi.price)                                AS product_revenue,
    SUM(oi.freight_value)                        AS freight_revenue,
    SUM(pay.payment_value)                       AS total_payment_recorded
FROM KEYA_MART.ORDERS o
INNER JOIN KEYA_MART.CUSTOMERS c    ON o.customer_id = c.customer_id
INNER JOIN KEYA_MART.ORDER_ITEMS oi ON o.order_id = oi.order_id
INNER JOIN KEYA_MART.PRODUCTS p     ON oi.product_id = p.product_id
INNER JOIN KEYA_MART.PAYMENTS pay   ON o.order_id = pay.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state, COALESCE(p.product_category_name, 'unknown')
ORDER BY product_revenue DESC;
'@ | Set-Content -Path "03_Week3_Optimization\sql\01_baseline_queries.sql" -Encoding UTF8; .\.venv\Scripts\python.exe -c "from pathlib import Path; txt = Path('03_Week3_Optimization/sql/01_baseline_queries.sql').read_text(encoding='utf-8'); print('Queries found:', sum(1 for i in range(1,11) if f'[Q{i:02d}]' in txt))"
