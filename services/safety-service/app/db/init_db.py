from app.db.base import Base, engine
from app.models.dispute import Dispute
from app.models.metric import PlatformMetric
from app.models.safety_report import SafetyReport


def init_db():
    Base.metadata.create_all(bind=engine)


