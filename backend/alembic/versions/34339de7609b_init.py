"""init

Revision ID: 34339de7609b
Revises:
Create Date: 2025-08-03 16:40:46.758197

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "34339de7609b"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""

    # ### end Alembic commands ###
