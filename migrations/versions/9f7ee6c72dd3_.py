"""empty message

Revision ID: 9f7ee6c72dd3
Revises: b00a1c6ca49d
Create Date: 2019-05-13 13:58:15.267976

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f7ee6c72dd3'
down_revision = 'b00a1c6ca49d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('score', sa.Column('bonus', sa.Integer(), nullable=True))
    op.add_column('score', sa.Column('distance', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('score', 'distance')
    op.drop_column('score', 'bonus')
    # ### end Alembic commands ###