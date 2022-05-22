"""Change data type od date_taken to datetime

Revision ID: 1bd71908eb3b
Revises: ffb7a91e19f5
Create Date: 2022-05-21 10:13:36.804770

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '1bd71908eb3b'
down_revision = 'ffb7a91e19f5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('tasks', 'date_taken', type_=sa.DATETIME, existing_type=sa.DATE)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('tasks', 'date_taken', type_=sa.DATE, existing_type=sa.DATETIME)
    # ### end Alembic commands ###
