"""empty message

Revision ID: 6fa758320ba5
Revises: 1d12308c8808
Create Date: 2019-03-28 14:06:26.729527

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6fa758320ba5'
down_revision = '1d12308c8808'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('team', sa.Column('is_open', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('team', 'is_open')
    # ### end Alembic commands ###
