"""search functions

Revision ID: 93bd3a53a2c8
Revises: d3cae92f15f4
Create Date: 2025-09-25 10:12:45.252654

"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy_searchable import sql_expressions

# revision identifiers, used by Alembic.
revision: str = "93bd3a53a2c8"
down_revision: Union[str, Sequence[str], None] = "d3cae92f15f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(sql_expressions.statement)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP FUNCTION parse_websearch(regconfig, text);")
    op.execute("DROP FUNCTION parse_websearch(text);")
