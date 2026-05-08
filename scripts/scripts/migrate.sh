#!/bin/bash

# Database Migration Script

set -e

echo "🗄️ Running database migrations..."

# PostgreSQL migrations
docker-compose -f infra/docker/docker-compose.yml exec postgres psql -U admin -d smart_travel << 'EOF'
-- Create pipeline_runs table if not exists
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id UUID PRIMARY KEY,
    city VARCHAR(50) NOT NULL,
    sources TEXT,
    status VARCHAR(20) DEFAULT 'running',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_city ON pipeline_runs(city);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON pipeline_runs(status);

-- Create places_metadata table for additional metadata
CREATE TABLE IF NOT EXISTS places_metadata (
    place_id VARCHAR(100) PRIMARY KEY,
    city VARCHAR(50) NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_count INTEGER DEFAULT 1,
    data_quality_score DECIMAL(3,2)
);

CREATE INDEX IF NOT EXISTS idx_places_metadata_city ON places_metadata(city);
EOF

echo "✅ PostgreSQL migrations completed"

# MongoDB indexes
docker-compose -f infra/docker/docker-compose.yml exec mongodb mongosh smart_travel -u admin -p "${MONGODB_PASSWORD}" --authenticationDatabase admin --eval "
db.places_bronze.createIndex({'city': 1, 'source': 1});
db.places_bronze.createIndex({'collected_at': 1});

db.places_silver.createIndex({'city': 1});
db.places_silver.createIndex({'deduplication_key': 1}, {unique: true});

db.places_gold.createIndex({'city': 1});
db.places_gold.createIndex({'categories': 1});
db.places_gold.createIndex({location: '2dsphere'});

print('✅ MongoDB indexes created');
"

echo "🎉 All migrations completed successfully!"
