"""empty message

Revision ID: 931a267005f9
Revises: 6060cae70531
Create Date: 2019-10-04 11:45:32.254006

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '931a267005f9'
down_revision = '6060cae70531'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('task', 'user_ip')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('task', sa.Column('user_ip', mysql.VARCHAR(length=128), nullable=True))
    # ### end Alembic commands ###
