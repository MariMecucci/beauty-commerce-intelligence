-- Fato analítico de receita mensal por categoria e marca.
-- Regra: receita apenas de pedidos completed. Valores em centavos.
WITH valid_sales AS (
    SELECT
        SUBSTR(o.order_date, 1, 7) AS sale_month,
        p.category,
        p.brand,
        o.order_id,
        i.quantity,
        i.quantity * i.unit_price_cents AS item_revenue_cents
    FROM order_items AS i
    INNER JOIN orders AS o ON i.order_id = o.order_id
    INNER JOIN products AS p ON i.product_id = p.product_id
    WHERE o.status = 'completed'
)
SELECT
    sale_month,
    category,
    brand,
    COUNT(DISTINCT order_id) AS order_count,
    SUM(quantity) AS units_sold,
    SUM(item_revenue_cents) AS revenue_brl_cents
FROM valid_sales
GROUP BY sale_month, category, brand
ORDER BY sale_month, revenue_brl_cents DESC, brand;
