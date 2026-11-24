-- =====================================================================
-- KEYA MART - PHASE 6: VERIFY DATA LOAD & RELATIONSHIPS
-- =====================================================================

-- 1. Verify exact row counts across all 8 tables
SELECT 'GEOLOCATION'   AS TABLE_NAME, COUNT(*) AS ROW_COUNT FROM KEYA_MART.GEOLOCATION
UNION ALL SELECT 'CUSTOMERS',     COUNT(*) FROM KEYA_MART.CUSTOMERS
UNION ALL SELECT 'SELLERS',       COUNT(*) FROM KEYA_MART.SELLERS
UNION ALL SELECT 'PRODUCTS',      COUNT(*) FROM KEYA_MART.PRODUCTS
UNION ALL SELECT 'ORDERS',        COUNT(*) FROM KEYA_MART.ORDERS
UNION ALL SELECT 'ORDER_ITEMS',   COUNT(*) FROM KEYA_MART.ORDER_ITEMS
UNION ALL SELECT 'PAYMENTS',      COUNT(*) FROM KEYA_MART.PAYMENTS
UNION ALL SELECT 'ORDER_REVIEWS', COUNT(*) FROM KEYA_MART.ORDER_REVIEWS;

-- 2. Test multi-table join across Orders, Customers, Items, and Products
SELECT TOP 10
    o.order_id,
    c.customer_city,
    c.customer_state,
    o.order_status,
    oi.order_item_id,
    p.product_category_name,
    oi.price,
    oi.freight_value
FROM KEYA_MART.ORDERS o
INNER JOIN KEYA_MART.CUSTOMERS c ON o.customer_id = c.customer_id
INNER JOIN KEYA_MART.ORDER_ITEMS oi ON o.order_id = oi.order_id
INNER JOIN KEYA_MART.PRODUCTS p ON oi.product_id = p.product_id;