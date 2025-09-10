"""search functions

Revision ID: 7025cce4f9dc
Revises: 5f6e6ffb6b7e
Create Date: 2025-09-11 00:16:31.392925

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy_searchable import sql_expressions


# revision identifiers, used by Alembic.
revision: str = "7025cce4f9dc"
down_revision: Union[str, Sequence[str], None] = "5f6e6ffb6b7e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(sql_expressions.statement)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP FUNCTION parse_websearch(regconfig, text);")
    op.execute("DROP FUNCTION parse_websearch(text);")
