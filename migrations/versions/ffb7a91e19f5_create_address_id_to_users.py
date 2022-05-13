"""create address_id to users

Revision ID: ffb7a91e19f5
Revises: 889ce27bcc1d
Create Date: 2022-05-12 07:48:02.957702

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ffb7a91e19f5'
down_revision = '889ce27bcc1d'
branch_labels = None
depends_on = None


def upgrade():
    # in users table, add column address_id which is Int and nullable
    op.add_column('users', sa.Column('address_id', sa.Integer(), nullable=True))

    # Then create a FK address_users_fk in users table with reference to address table
    # using column address_id in users table and column id in address table
    # Cascade on delete
    op.create_foreign_key('address_users_fk', source_table="users", referent_table="address",
                          local_cols=['address_id'], remote_cols=["id"],
                          ondelete="CASCADE")


def downgrade():
    # First we need to drop fk from users table
    op.drop_constraint('address_users_fk', table_name="users")
    # Then drop column address_id in users table
    op.drop_column('users', 'address_id')

