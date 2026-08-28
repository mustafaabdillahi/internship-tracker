"""added fields to stageevent and emailprocessing2

Revision ID: 6665d5cc801a
Revises: 34690ee79fe9
Create Date: 2026-08-28 00:47:31.966647

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6665d5cc801a'
down_revision: Union[str, Sequence[str], None] = '34690ee79fe9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Create PostgreSQL enum types before using them in columns.
    deadline_type = sa.Enum(
        'OA',
        'APPLICATION',
        'INTERVIEW_CONFIRMATION',
        'DOCUMENT_SUBMISSION',
        'OTHER',
        name='deadlinetype',
    )

    interview_type = sa.Enum(
        'PHONE',
        'VIDEO',
        'TECHNICAL',
        'BEHAVIOURAL',
        'ASSESSMENT',
        'ONSITE',
        'OTHER',
        name='interviewtype',
    )

    deadline_type.create(op.get_bind(), checkfirst=True)
    interview_type.create(op.get_bind(), checkfirst=True)

    # Add columns.
    op.add_column(
        'email_processing',
        sa.Column('next_action', sa.Text(), nullable=True)
    )

    op.add_column(
        'stage_event',
        sa.Column(
            'deadline',
            sa.DateTime(timezone=True),
            nullable=True
        )
    )

    op.add_column(
        'stage_event',
        sa.Column(
            'deadline_type',
            deadline_type,
            nullable=True
        )
    )

    op.add_column(
        'stage_event',
        sa.Column(
            'interview_date',
            sa.DateTime(timezone=True),
            nullable=True
        )
    )

    op.add_column(
        'stage_event',
        sa.Column(
            'interview_type',
            interview_type,
            nullable=True
        )
    )

    op.add_column(
        'stage_event',
        sa.Column('notes', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""

    # Remove columns first because they depend on the enum types.
    op.drop_column('stage_event', 'notes')
    op.drop_column('stage_event', 'interview_type')
    op.drop_column('stage_event', 'interview_date')
    op.drop_column('stage_event', 'deadline_type')
    op.drop_column('stage_event', 'deadline')
    op.drop_column('email_processing', 'next_action')

    # Then remove the PostgreSQL enum types.
    interview_type = sa.Enum(
        'PHONE',
        'VIDEO',
        'TECHNICAL',
        'BEHAVIOURAL',
        'ASSESSMENT',
        'ONSITE',
        'OTHER',
        name='interviewtype',
    )

    deadline_type = sa.Enum(
        'OA',
        'APPLICATION',
        'INTERVIEW_CONFIRMATION',
        'DOCUMENT_SUBMISSION',
        'OTHER',
        name='deadlinetype',
    )

    interview_type.drop(op.get_bind(), checkfirst=True)
    deadline_type.drop(op.get_bind(), checkfirst=True)
