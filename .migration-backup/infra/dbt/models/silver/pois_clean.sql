{{ config(
    materialized='incremental',
    unique_key='u_key'
) }}

WITH osm_src AS (
    -- Giả định đã có bảng bronze_osm nạp từ MinIO/Fivetran hoặc tương tự vào Postgres
    SELECT * FROM {{ source('lakehouse', 'bronze_osm') }}
),
google_src AS (
    -- Giả định đã có bảng bronze_google
    SELECT * FROM {{ source('lakehouse', 'bronze_google') }}
)

SELECT
    o.u_key,
    COALESCE(g.name, o.name)     AS name,
    COALESCE(g.rating, o.rating) AS rating,
    COALESCE(g.review_count, o.review_count) AS review_count,
    o.city,
    o.category,
    o.geom,
    -- Source tracking (Lineage)
    o.u_key                       AS osm_source_key,
    g.place_id                    AS google_place_id,
    CURRENT_TIMESTAMP             AS silver_updated_at
FROM osm_src o
LEFT JOIN google_src g USING (u_key)
WHERE o.name IS NOT NULL
{% if is_incremental() %}
  AND o.updated_at > (SELECT max(silver_updated_at) FROM {{ this }})
{% endif %}
