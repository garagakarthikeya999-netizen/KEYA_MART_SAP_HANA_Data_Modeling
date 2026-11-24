-- =====================================================================
-- KEYA MART - PHASE 6: SCHEMA AND PHYSICAL TABLE CREATION (SAP HANA)
-- =====================================================================

-- 1. Create Project Schema
CREATE SCHEMA KEYA_MART;
SET SCHEMA KEYA_MART;

-- 2. Table 1: GEOLOCATION (Deduplicated Lookup Table - 19,015 zip prefixes)
CREATE COLUMN TABLE KEYA_MART.GEOLOCATION (
    geolocation_zip_code_prefix INTEGER NOT NULL,
    geolocation_lat             DECIMAL(10, 6),
    geolocation_lng             DECIMAL(10, 6),
    geolocation_city            NVARCHAR(100),
    geolocation_state           NVARCHAR(5),
    CONSTRAINT PK_GEOLOCATION PRIMARY KEY (geolocation_zip_code_prefix)
);

-- 3. Table 2: CUSTOMERS
CREATE COLUMN TABLE KEYA_MART.CUSTOMERS (
    customer_id              NVARCHAR(36) NOT NULL,
    customer_unique_id       NVARCHAR(36) NOT NULL,
    customer_zip_code_prefix INTEGER NOT NULL,
    customer_city            NVARCHAR(100),
    customer_state           NVARCHAR(5),
    CONSTRAINT PK_CUSTOMERS PRIMARY KEY (customer_id)
);

-- 4. Table 3: SELLERS
CREATE COLUMN TABLE KEYA_MART.SELLERS (
    seller_id              NVARCHAR(36) NOT NULL,
    seller_zip_code_prefix INTEGER NOT NULL,
    seller_city            NVARCHAR(100),
    seller_state           NVARCHAR(5),
    CONSTRAINT PK_SELLERS PRIMARY KEY (seller_id)
);

-- 5. Table 4: PRODUCTS
CREATE COLUMN TABLE KEYA_MART.PRODUCTS (
    product_id                 NVARCHAR(36) NOT NULL,
    product_category_name      NVARCHAR(100),
    product_name_lenght        DECIMAL(10, 0),
    product_description_lenght DECIMAL(10, 0),
    product_photos_qty         DECIMAL(10, 0),
    product_weight_g           DECIMAL(10, 0),
    product_length_cm          DECIMAL(10, 0),
    product_height_cm          DECIMAL(10, 0),
    product_width_cm           DECIMAL(10, 0),
    CONSTRAINT PK_PRODUCTS PRIMARY KEY (product_id)
);

-- 6. Table 5: ORDERS
CREATE COLUMN TABLE KEYA_MART.ORDERS (
    order_id                      NVARCHAR(36) NOT NULL,
    customer_id                   NVARCHAR(36) NOT NULL,
    order_status                  NVARCHAR(20) NOT NULL,
    order_purchase_timestamp      TIMESTAMP NOT NULL,
    order_approved_at             TIMESTAMP,
    order_delivered_carrier_date  TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP,
    CONSTRAINT PK_ORDERS PRIMARY KEY (order_id),
    CONSTRAINT FK_ORDERS_CUSTOMERS FOREIGN KEY (customer_id)
        REFERENCES KEYA_MART.CUSTOMERS (customer_id)
);

-- 7. Table 6: ORDER_ITEMS (Composite PK)
CREATE COLUMN TABLE KEYA_MART.ORDER_ITEMS (
    order_id            NVARCHAR(36) NOT NULL,
    order_item_id       INTEGER NOT NULL,
    product_id          NVARCHAR(36) NOT NULL,
    seller_id           NVARCHAR(36) NOT NULL,
    shipping_limit_date TIMESTAMP NOT NULL,
    price               DECIMAL(12, 2) NOT NULL,
    freight_value       DECIMAL(12, 2) NOT NULL,
    CONSTRAINT PK_ORDER_ITEMS PRIMARY KEY (order_id, order_item_id),
    CONSTRAINT FK_ITEMS_ORDERS FOREIGN KEY (order_id)
        REFERENCES KEYA_MART.ORDERS (order_id),
    CONSTRAINT FK_ITEMS_PRODUCTS FOREIGN KEY (product_id)
        REFERENCES KEYA_MART.PRODUCTS (product_id),
    CONSTRAINT FK_ITEMS_SELLERS FOREIGN KEY (seller_id)
        REFERENCES KEYA_MART.SELLERS (seller_id)
);

-- 8. Table 7: PAYMENTS (Composite PK)
CREATE COLUMN TABLE KEYA_MART.PAYMENTS (
    order_id             NVARCHAR(36) NOT NULL,
    payment_sequential   INTEGER NOT NULL,
    payment_type         NVARCHAR(30) NOT NULL,
    payment_installments INTEGER NOT NULL,
    payment_value        DECIMAL(12, 2) NOT NULL,
    CONSTRAINT PK_PAYMENTS PRIMARY KEY (order_id, payment_sequential),
    CONSTRAINT FK_PAYMENTS_ORDERS FOREIGN KEY (order_id)
        REFERENCES KEYA_MART.ORDERS (order_id)
);

-- 9. Table 8: ORDER_REVIEWS (Composite PK)
CREATE COLUMN TABLE KEYA_MART.ORDER_REVIEWS (
    review_id               NVARCHAR(36) NOT NULL,
    order_id                NVARCHAR(36) NOT NULL,
    review_score            INTEGER NOT NULL,
    review_comment_title    NVARCHAR(255),
    review_comment_message  NVARCHAR(2000),
    review_creation_date    TIMESTAMP,
    review_answer_timestamp TIMESTAMP,
    CONSTRAINT PK_ORDER_REVIEWS PRIMARY KEY (review_id, order_id),
    CONSTRAINT FK_REVIEWS_ORDERS FOREIGN KEY (order_id)
        REFERENCES KEYA_MART.ORDERS (order_id)
);