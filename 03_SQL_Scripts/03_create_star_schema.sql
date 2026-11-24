-- =====================================================================
-- KEYA MART - PHASE 7: ANALYTICAL STAR SCHEMA (4 DIMENSIONS + 1 FACT)
-- =====================================================================
SET SCHEMA KEYA_MART;

-- 1. DIM_CUSTOMER (Enriched with Geolocation Lat/Lng via LEFT JOIN)
CREATE COLUMN TABLE KEYA_MART.DIM_CUSTOMER (
    customer_sk              INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1) PRIMARY KEY,
    customer_id              NVARCHAR(36) NOT NULL,
    customer_unique_id       NVARCHAR(36) NOT NULL,
    customer_zip_code_prefix INTEGER NOT NULL,
    customer_city            NVARCHAR(100),
    customer_state           NVARCHAR(5),
    customer_lat             DECIMAL(10, 6),
    customer_lng             DECIMAL(10, 6)
);

INSERT INTO KEYA_MART.DIM_CUSTOMER (
    customer_id, customer_unique_id, customer_zip_code_prefix,
    customer_city, customer_state, customer_lat, customer_lng
)
SELECT
    c.customer_id,
    c.customer_unique_id,
    c.customer_zip_code_prefix,
    c.customer_city,
    c.customer_state,
    g.geolocation_lat,
    g.geolocation_lng
FROM KEYA_MART.CUSTOMERS c
LEFT JOIN KEYA_MART.GEOLOCATION g
    ON c.customer_zip_code_prefix = g.geolocation_zip_code_prefix;

-- 2. DIM_PRODUCT
CREATE COLUMN TABLE KEYA_MART.DIM_PRODUCT (
    product_sk            INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1) PRIMARY KEY,
    product_id            NVARCHAR(36) NOT NULL,
    product_category_name NVARCHAR(100),
    product_photos_qty    DECIMAL(10, 0),
    product_weight_g      DECIMAL(10, 0)
);

INSERT INTO KEYA_MART.DIM_PRODUCT (
    product_id, product_category_name, product_photos_qty, product_weight_g
)
SELECT
    product_id,
    COALESCE(product_category_name, 'unknown'),
    product_photos_qty,
    product_weight_g
FROM KEYA_MART.PRODUCTS;

-- 3. DIM_SELLER (Enriched with Geolocation Lat/Lng via LEFT JOIN)
CREATE COLUMN TABLE KEYA_MART.DIM_SELLER (
    seller_sk              INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1) PRIMARY KEY,
    seller_id              NVARCHAR(36) NOT NULL,
    seller_zip_code_prefix INTEGER NOT NULL,
    seller_city            NVARCHAR(100),
    seller_state           NVARCHAR(5),
    seller_lat             DECIMAL(10, 6),
    seller_lng             DECIMAL(10, 6)
);

INSERT INTO KEYA_MART.DIM_SELLER (
    seller_id, seller_zip_code_prefix, seller_city,
    seller_state, seller_lat, seller_lng
)
SELECT
    s.seller_id,
    s.seller_zip_code_prefix,
    s.seller_city,
    s.seller_state,
    g.geolocation_lat,
    g.geolocation_lng
FROM KEYA_MART.SELLERS s
LEFT JOIN KEYA_MART.GEOLOCATION g
    ON s.seller_zip_code_prefix = g.geolocation_zip_code_prefix;

-- 4. DIM_DATE (Smart integer key YYYYMMDD)
CREATE COLUMN TABLE KEYA_MART.DIM_DATE (
    date_sk      INTEGER PRIMARY KEY,
    full_date    DATE NOT NULL,
    year_num     INTEGER NOT NULL,
    quarter_num  INTEGER NOT NULL,
    month_num    INTEGER NOT NULL,
    month_name   NVARCHAR(20) NOT NULL,
    day_name     NVARCHAR(10) NOT NULL,
    is_weekend   NVARCHAR(3) NOT NULL
);

INSERT INTO KEYA_MART.DIM_DATE (
    date_sk, full_date, year_num, quarter_num,
    month_num, month_name, day_name, is_weekend
)
SELECT DISTINCT
    TO_INTEGER(TO_VARCHAR(o.order_purchase_timestamp, 'YYYYMMDD')) AS date_sk,
    TO_DATE(o.order_purchase_timestamp) AS full_date,
    YEAR(o.order_purchase_timestamp) AS year_num,
    CEIL(MONTH(o.order_purchase_timestamp) / 3.0) AS quarter_num,
    MONTH(o.order_purchase_timestamp) AS month_num,
    TO_VARCHAR(o.order_purchase_timestamp, 'MONTH') AS month_name,
    TO_VARCHAR(o.order_purchase_timestamp, 'DY') AS day_name,
    CASE WHEN WEEKDAY(o.order_purchase_timestamp) IN (5, 6) THEN 'Yes' ELSE 'No' END AS is_weekend
FROM KEYA_MART.ORDERS o;

-- 5. FACT_SALES (Grain: 1 row per Order Item = 112,650 rows)
CREATE COLUMN TABLE KEYA_MART.FACT_SALES (
    sales_sk         INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1) PRIMARY KEY,
    order_id         NVARCHAR(36) NOT NULL,
    order_item_id    INTEGER NOT NULL,
    customer_sk      INTEGER NOT NULL,
    product_sk       INTEGER NOT NULL,
    seller_sk        INTEGER NOT NULL,
    date_sk          INTEGER NOT NULL,
    order_status     NVARCHAR(20) NOT NULL,
    item_quantity    INTEGER NOT NULL,
    item_price       DECIMAL(12, 2) NOT NULL,
    freight_value    DECIMAL(12, 2) NOT NULL,
    total_item_value DECIMAL(12, 2) NOT NULL,
    delivery_days    INTEGER,
    avg_review_score DECIMAL(4, 2),
    CONSTRAINT FK_FACT_CUSTOMER FOREIGN KEY (customer_sk) REFERENCES KEYA_MART.DIM_CUSTOMER (customer_sk),
    CONSTRAINT FK_FACT_PRODUCT  FOREIGN KEY (product_sk)  REFERENCES KEYA_MART.DIM_PRODUCT  (product_sk),
    CONSTRAINT FK_FACT_SELLER   FOREIGN KEY (seller_sk)   REFERENCES KEYA_MART.DIM_SELLER   (seller_sk),
    CONSTRAINT FK_FACT_DATE     FOREIGN KEY (date_sk)     REFERENCES KEYA_MART.DIM_DATE     (date_sk)
);

INSERT INTO KEYA_MART.FACT_SALES (
    order_id, order_item_id, customer_sk, product_sk, seller_sk, date_sk,
    order_status, item_quantity, item_price, freight_value, total_item_value,
    delivery_days, avg_review_score
)
SELECT
    oi.order_id,
    oi.order_item_id,
    dc.customer_sk,
    dp.product_sk,
    ds.seller_sk,
    TO_INTEGER(TO_VARCHAR(o.order_purchase_timestamp, 'YYYYMMDD')) AS date_sk,
    o.order_status,
    1 AS item_quantity,
    oi.price AS item_price,
    oi.freight_value,
    (oi.price + oi.freight_value) AS total_item_value,
    DAYS_BETWEEN(o.order_purchase_timestamp, o.order_delivered_customer_date) AS delivery_days,
    rev.avg_review_score
FROM KEYA_MART.ORDER_ITEMS oi
INNER JOIN KEYA_MART.ORDERS o         ON oi.order_id = o.order_id
INNER JOIN KEYA_MART.DIM_CUSTOMER dc  ON o.customer_id = dc.customer_id
INNER JOIN KEYA_MART.DIM_PRODUCT dp   ON oi.product_id = dp.product_id
INNER JOIN KEYA_MART.DIM_SELLER ds    ON oi.seller_id = ds.seller_id
LEFT JOIN (
    SELECT order_id, AVG(CAST(review_score AS DECIMAL(4, 2))) AS avg_review_score
    FROM KEYA_MART.ORDER_REVIEWS
    GROUP BY order_id
) rev ON oi.order_id = rev.order_id;