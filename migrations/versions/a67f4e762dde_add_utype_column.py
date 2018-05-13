"""add utype column

Revision ID: a67f4e762dde
Revises: bdd54c814841
Create Date: 2018-01-27 16:21:49.919935

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a67f4e762dde'
down_revision = 'bdd54c814841'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('utype', sa.String(length=8), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'utype')
    # ### end Alembic commands ###