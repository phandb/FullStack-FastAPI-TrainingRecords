"""Create address table

Revision ID: 889ce27bcc1d
Revises: 391765a4a04d
Create Date: 2022-05-11 07:47:40.205197

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '889ce27bcc1d'
down_revision = '391765a4a04d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('address',
                    sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
                    sa.Column('address1', sa.String(100), nullable=False),
                    sa.Column('address2', sa.String(80), nullable=False),
                    sa.Column('city', sa.String(50), nullable=False),
                    sa.Column('state', sa.String(50), nullable=False),
                    sa.Column('country', sa.String(50), nullable=False),
                    sa.Column('postal_code', sa.String(20), nullable=False)
                    )


def downgrade():
    op.drop_table('address')
