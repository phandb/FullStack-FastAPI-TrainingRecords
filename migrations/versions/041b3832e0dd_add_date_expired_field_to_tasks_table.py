"""Add date_expired field to tasks table

Revision ID: 041b3832e0dd
Revises: 00701e6175f3
Create Date: 2022-05-24 22:25:39.516594

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '041b3832e0dd'
down_revision = '00701e6175f3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tasks', sa.Column('date_expired', sa.DATETIME, nullable=True))


def downgrade():
    op.drop_column('tasks', 'date_expired')
