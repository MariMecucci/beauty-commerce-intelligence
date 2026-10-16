-- Ranking mensal com window function: excelente evidência de SQL analítico.
WITH product_sales AS (
    SELECT
        SUBSTR(o.order_date, 1, 7) AS sale_month,
        p.product_id,
        p.product_name,
        p.brand,
        p.category,
        SUM(i.quantity) AS units_sold,
        SUM(i.quantity * i.unit_price_cents) AS revenue_brl_cents
    FROM orders AS o
    JOIN order_items AS i ON o.order_id = i.order_id
    JOIN products AS p ON p.product_id = i.product_id
    WHERE o.status = 'completed'
    GROUP BY sale_month, p.product_id, p.product_name, p.brand, p.category
)
SELECT
    *,
    DENSE_RANK() OVER (
        PARTITION BY sale_month
        ORDER BY revenue_brl_cents DESC
    ) AS revenue_rank_in_month
FROM product_sales
ORDER BY sale_month, revenue_rank_in_month, product_id;
