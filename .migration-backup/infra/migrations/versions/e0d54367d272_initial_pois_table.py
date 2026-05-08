"""initial_pois_table

Revision ID: e0d54367d272
Revises: 
Create Date: 2026-04-25 16:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry

# revision identifiers, used by Alembic.
revision = 'e0d54367d272'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Enable PostGIS extension if not exists
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # 2. Create Table POIs
    op.create_table(
        'pois',
        sa.Column('u_key', sa.String(16), primary_key=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('city', sa.String(50)),
        sa.Column('category', sa.String(50)),
        sa.Column('rating', sa.Numeric(3, 1)),
        sa.Column('review_count', sa.Integer()),
        sa.Column('geom', Geometry('POINT', srid=4326), nullable=False),
        sa.Column('metadata', sa.JSON()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )

    # 3. Create Indexes
    op.create_index('idx_pois_geom', 'pois', ['geom'], postgresql_using='gist')
    op.create_index('idx_pois_city', 'pois', ['city'])
    op.create_index('idx_pois_rating', 'pois', [sa.text('rating DESC')])
    op.create_index('idx_pois_meta', 'pois', ['metadata'], postgresql_using='gin')

def downgrade() -> None:
    op.drop_table('pois')
