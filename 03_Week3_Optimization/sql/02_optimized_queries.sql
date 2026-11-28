-- =====================================================================
-- KEYA MART - WEEK 3: OPTIMIZED ANALYTICAL BENCHMARK QUERIES (Q01 - Q10)
-- =====================================================================

-- [Q01] Total Sales Revenue (Single-Pass Column-Pruned Scan)
SELECT
    COUNT(DISTINCT order_id)        AS total_orders,
    SUM(item_quantity)              AS total_items_sold,
    SUM(item_price)                 AS product_revenue,
    SUM(freight_value)              AS total_freight,
    SUM(total_item_value)           AS gross_revenue,
    ROUND(AVG(total_item_value), 2) AS avg_item_value
FROM KEYA_MART.FACT_SALES
WHERE order_status = 'delivered';

-- [Q02] Monthly Revenue Analysis (Direct FACT_SALES + DIM_DATE Join, Bypassing 4-Join Cube View)
SELECT
    d.year_num,
    d.month_num,
    d.month_name,
    COUNT(DISTINCT f.order_id)        AS total_orders,
    SUM(f.item_quantity)              AS total_items_sold,
    SUM(f.total_item_value)           AS gross_revenue,
    ROUND(AVG(f.total_item_value), 2) AS avg_item_value
FROM KEYA_MART.FACT_SALES f
INNER JOIN KEYA_MART.DIM_DATE d ON f.date_sk = d.date_sk
WHERE f.order_status = 'delivered'
GROUP BY d.year_num, d.month_num, d.month_name
ORDER BY d.year_num, d.month_num;

-- [Q03] Top-Selling Product Categories (Direct FACT_SALES + DIM_PRODUCT Join, Bypassing Nested Views)
SELECT TOP 10
    p.product_category_name,
    COUNT(DISTINCT f.order_id)        AS total_orders,
    SUM(f.item_quantity)              AS total_items_sold,
    SUM(f.item_price)                 AS product_revenue,
    SUM(f.total_item_value)           AS gross_revenue,
    ROUND(AVG(f.avg_review_score), 2) AS avg_review_score,
    ROUND(AVG(f.delivery_days), 1)    AS avg_delivery_days
FROM KEYA_MART.FACT_SALES f
INNER JOIN KEYA_MART.DIM_PRODUCT p ON f.product_sk = p.product_sk
WHERE f.order_status = 'delivered'
GROUP BY p.product_category_name
ORDER BY gross_revenue DESC;

-- [Q04] Top-Performing Sellers (Pre-Aggregate by Surrogate Key Before Dimension Join)
WITH seller_agg AS (
    SELECT
        seller_sk,
        COUNT(DISTINCT order_id)        AS total_orders,
        SUM(item_quantity)              AS total_items_sold,
        SUM(total_item_value)           AS gross_revenue,
        ROUND(AVG(avg_review_score), 2) AS avg_review_score
    FROM KEYA_MART.FACT_SALES
    WHERE order_status = 'delivered'
    GROUP BY seller_sk
)
SELECT TOP 10
    s.seller_id,
    s.seller_city,
    s.seller_state,
    a.total_orders,
    a.total_items_sold,
    a.gross_revenue,
    a.avg_review_score
FROM seller_agg a
INNER JOIN KEYA_MART.DIM_SELLER s ON a.seller_sk = s.seller_sk
ORDER BY a.gross_revenue DESC;

-- [Q05] Customer Purchase Analysis (Pre-Filtered & Column-Pruned CTEs)
WITH deliv_fact AS (
    SELECT customer_sk, order_id, item_quantity, total_item_value
    FROM KEYA_MART.FACT_SALES
    WHERE order_status = 'delivered'
),
cust_dim AS (
    SELECT customer_sk, customer_unique_id, customer_state
    FROM KEYA_MART.DIM_CUSTOMER
)
SELECT TOP 20
    c.customer_unique_id,
    c.customer_state,
    COUNT(DISTINCT f.order_id)        AS total_orders,
    SUM(f.item_quantity)              AS total_items_bought,
    SUM(f.total_item_value)           AS total_spend,
    ROUND(AVG(f.total_item_value), 2) AS avg_item_spend
FROM deliv_fact f
INNER JOIN cust_dim c ON f.customer_sk = c.customer_sk
GROUP BY c.customer_unique_id, c.customer_state
HAVING COUNT(DISTINCT f.order_id) > 1
ORDER BY total_spend DESC;

-- [Q06] State-Wise Sales Analysis (Direct FACT_SALES + DIM_CUSTOMER Join, Bypassing View)
SELECT
    c.customer_state,
    COUNT(DISTINCT f.order_id) AS total_orders,
    SUM(f.item_quantity)       AS total_items_sold,
    SUM(f.total_item_value)    AS gross_revenue
FROM KEYA_MART.FACT_SALES f
INNER JOIN KEYA_MART.DIM_CUSTOMER c ON f.customer_sk = c.customer_sk
WHERE f.order_status = 'delivered'
GROUP BY c.customer_state
ORDER BY gross_revenue DESC;

-- [Q07] Order Status Analysis (Single-Pass Window Function)
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

-- [Q08] Average Delivery Time vs. Estimated Delivery (Filter & Column-Prune ORDERS First)
WITH delivered_orders AS (
    SELECT
        customer_id,
        DAYS_BETWEEN(order_purchase_timestamp, order_delivered_customer_date) AS actual_days,
        DAYS_BETWEEN(order_purchase_timestamp, order_estimated_delivery_date) AS est_days,
        CASE WHEN order_delivered_customer_date > order_estimated_delivery_date THEN 1 ELSE 0 END AS is_late
    FROM KEYA_MART.ORDERS
    WHERE order_status = 'delivered'
      AND order_delivered_customer_date IS NOT NULL
)
SELECT
    c.customer_state,
    COUNT(*)                        AS delivered_orders,
    ROUND(AVG(d.actual_days), 2)    AS avg_actual_delivery_days,
    ROUND(AVG(d.est_days), 2)       AS avg_estimated_delivery_days,
    SUM(d.is_late)                  AS late_orders
FROM delivered_orders d
INNER JOIN KEYA_MART.CUSTOMERS c ON d.customer_id = c.customer_id
GROUP BY c.customer_state
ORDER BY avg_actual_delivery_days DESC;

-- [Q09] Payment Type Analysis (Filter Delivered Orders Before Joining PAYMENTS)
WITH delivered_ids AS (
    SELECT order_id
    FROM KEYA_MART.ORDERS
    WHERE order_status = 'delivered'
)
SELECT
    p.payment_type,
    COUNT(*)                              AS payment_transactions,
    COUNT(DISTINCT p.order_id)            AS unique_orders,
    SUM(p.payment_value)                  AS total_payment_value,
    ROUND(AVG(p.payment_value), 2)        AS avg_payment_value,
    ROUND(AVG(p.payment_installments), 2) AS avg_installments
FROM KEYA_MART.PAYMENTS p
INNER JOIN delivered_ids o ON p.order_id = o.order_id
GROUP BY p.payment_type
ORDER BY total_payment_value DESC;

-- [Q10] Complex Multi-Table OLTP Join (Early Filtering + Column-Pruned CTEs)
WITH deliv_orders AS (
    SELECT order_id, customer_id
    FROM KEYA_MART.ORDERS
    WHERE order_status = 'delivered'
),
cust_state AS (
    SELECT customer_id, customer_state
    FROM KEYA_MART.CUSTOMERS
),
prod_cat AS (
    SELECT product_id, COALESCE(product_category_name, 'unknown') AS product_category_name
    FROM KEYA_MART.PRODUCTS
)
SELECT TOP 20
    c.customer_state,
    p.product_category_name,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(*)                   AS total_items,
    SUM(oi.price)              AS product_revenue,
    SUM(oi.freight_value)      AS freight_revenue,
    SUM(pay.payment_value)     AS total_payment_recorded
FROM deliv_orders o
INNER JOIN cust_state c            ON o.customer_id = c.customer_id
INNER JOIN KEYA_MART.ORDER_ITEMS oi ON o.order_id = oi.order_id
INNER JOIN prod_cat p              ON oi.product_id = p.product_id
INNER JOIN KEYA_MART.PAYMENTS pay  ON o.order_id = pay.order_id
GROUP BY c.customer_state, p.product_category_name
ORDER BY product_revenue DESC;