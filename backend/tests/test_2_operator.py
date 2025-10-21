import pytest
from backend.models import DataSource, DataSourceVersion, Service
from backend.tasks.import_txc_new import TXCImporter

from backend.deps import STATIC_DATA_DIR
from backend.config import get_logger, setup_logging

log = get_logger(__name__)


@pytest.mark.asyncio
async def test_2_operators(db_session):
    setup_logging()
    ds1 = DataSource(name="MoreBus")
    ds2 = DataSource(name="Salisbury Reds")

    db_session.add_all([ds1, ds2])
    db_session.flush()
    ds1_id = ds1.id
    ds2_id = ds2.id

    dsv1 = DataSourceVersion(data_source_id=ds1.id, name="MoreBus")
    dsv2 = DataSourceVersion(data_source_id=ds2.id, name="Salisbury Reds")

    db_session.add_all([dsv1, dsv2])
    db_session.flush()

    dsv1_id = dsv1.id
    dsv2_id = dsv2.id

    db_session.commit()

    mb_dir = STATIC_DATA_DIR / "test" / "morebus"

    txc_importer_mb = TXCImporter(
        mb_dir, ds_id=ds1_id, dsv_id=dsv1_id, skip_checks=False
    )
    txc_importer_mb.db = db_session
    await txc_importer_mb.import_folder()

    services = db_session.query(Service).all()
    assert len(services) > 0

    sr_dir = STATIC_DATA_DIR / "test" / "salisbury"

    txc_importer_sr = TXCImporter(
        sr_dir, ds_id=ds2_id, dsv_id=dsv2_id, skip_checks=False
    )
    txc_importer_sr.db = db_session
    await txc_importer_sr.import_folder()

    services = db_session.query(Service).all()

    for service in services:
        print(service)
        print(f"journeys: {len(service.journeys)}")
    assert len(services) == 1  # there should only be one service as it is a joint route
