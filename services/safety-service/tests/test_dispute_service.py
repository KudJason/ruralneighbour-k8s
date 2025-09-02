from uuid import UUID

import pytest
from app.schemas.dispute import DisputeCreate, DisputeStatus, DisputeUpdate
from app.services.dispute_service import DisputeService


class TestDisputeService:
    @pytest.fixture
    def sample_dispute(self):
        return DisputeCreate(
            service_assignment_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            complainant_id=UUID("550e8400-e29b-41d4-a716-446655440001"),
            respondent_id=UUID("550e8400-e29b-41d4-a716-446655440002"),
            dispute_type="quality",
            description="Service quality issue",
        )

    def test_file_dispute(self, db_session, sample_dispute):
        result = DisputeService.file_dispute(db_session, sample_dispute)
        assert result.dispute_type == sample_dispute.dispute_type
        assert result.status == DisputeStatus.OPEN

    def test_update_dispute_resolve(self, db_session, sample_dispute):
        created = DisputeService.file_dispute(db_session, sample_dispute)
        updated = DisputeService.update_dispute(
            db_session,
            str(created.dispute_id),
            DisputeUpdate(
                status=DisputeStatus.RESOLVED, resolution_notes="Refund issued"
            ),
        )
        assert updated is not None
        assert updated.status == DisputeStatus.RESOLVED
        assert updated.resolution_notes == "Refund issued"
