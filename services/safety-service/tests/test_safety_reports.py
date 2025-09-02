from uuid import UUID

import pytest
from app.crud.safety_report import safety_report_crud
from app.schemas.safety_report import SafetyReportCreate, SafetyReportUpdate


class TestSafetyReports:
    @pytest.fixture
    def sample_report(self):
        return SafetyReportCreate(
            reporter_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            reported_user_id=UUID("550e8400-e29b-41d4-a716-446655440001"),
            incident_type="harassment",
            incident_description="Inappropriate behavior",
        )

    def test_create_report(self, db_session, sample_report):
        created = safety_report_crud.create(db_session, sample_report)
        assert str(created.reporter_id) == str(sample_report.reporter_id)
        assert created.incident_type == sample_report.incident_type

    def test_update_report(self, db_session, sample_report):
        created = safety_report_crud.create(db_session, sample_report)
        updated = safety_report_crud.update(
            db_session, str(created.report_id), SafetyReportUpdate(status="in_review")
        )
        assert updated is not None
        status_value = updated.__dict__.get("status")
        assert status_value == "in_review"
