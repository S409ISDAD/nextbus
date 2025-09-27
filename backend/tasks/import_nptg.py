import sys
import xml.etree.ElementTree as ET

from sqlalchemy_searchable import sync_trigger

from backend.config import get_logger, setup_logging
from backend.db.db import SessionLocal, engine
from backend.deps import STATIC_DATA_DIR
from backend.models import AdminArea, District, Locality, Region
from backend.utils.download_to_static import download_to_static
from backend.utils.location import generate_point
from backend.utils.time import to_datetime

log = get_logger()


def handle_region(element: ET.Element):
    for region_element in element:
        region = Region(
            id=region_element.findtext("RegionCode"),
            name=region_element.findtext("Name"),
            created_at=to_datetime(region_element.attrib["CreationDateTime"]),
            modified_at=to_datetime(region_element.attrib["ModificationDateTime"]),
        )

        yield region

        for admin_area_element in region_element.find("AdministrativeAreas"):
            admin_area = AdminArea(
                id=int(admin_area_element.findtext("AdministrativeAreaCode")),
                atco_code=admin_area_element.findtext("AtcoAreaCode"),
                name=admin_area_element.findtext("Name"),
                short_name=admin_area_element.findtext("ShortName", ""),
                country=region_element.findtext("Country")[:3],
                created_at=to_datetime(admin_area_element.attrib["CreationDateTime"]),
                modified_at=to_datetime(
                    admin_area_element.attrib["ModificationDateTime"]
                ),
                region_id=region.id,
            )
            yield admin_area

            for district_element in admin_area_element.findall(
                "NptgDistricts/NptgDistrict"
            ):
                district = District(
                    id=int(district_element.findtext("NptgDistrictCode")),
                    name=district_element.findtext("Name"),
                    created_at=to_datetime(district_element.attrib["CreationDateTime"]),
                    modified_at=to_datetime(
                        district_element.attrib["ModificationDateTime"]
                    ),
                    admin_area_id=admin_area.id,
                )
                yield district


def handle_locality(element: ET.Element):
    for locality_element in element:
        district_id = locality_element.findtext("NptgDistrictRef")
        if district_id == "310":
            district_id = None
        lon = locality_element.findtext("Location/Translation/Longitude")
        lat = locality_element.findtext("Location/Translation/Latitude")
        yield Locality(
            id=locality_element.findtext("NptgLocalityCode"),
            name=locality_element.findtext("Descriptor/LocalityName"),
            qualifier_name=locality_element.findtext(
                "Descriptor/Qualify/QualifierName", ""
            ),
            created_at=to_datetime(locality_element.attrib["CreationDateTime"]),
            modified_at=to_datetime(locality_element.attrib["ModificationDateTime"]),
            admin_area_id=int(locality_element.findtext("AdministrativeAreaRef")),
            parent_id=locality_element.findtext("ParentNptgLocalityRef"),
            district_id=district_id,
            point=generate_point(lat, lon),
        )


def import_nptg_data():
    log.debug("Importing NPTG data...")
    with SessionLocal() as db:
        try:
            file = STATIC_DATA_DIR / "NPTG.xml"

            regions: dict[str, Region] = {r.id: r for r in db.query(Region).all()}
            admin_areas: dict[int, AdminArea] = {
                a.id: a for a in db.query(AdminArea).all()
            }
            districts: dict[int, District] = {d.id: d for d in db.query(District).all()}
            localities: dict[str, Locality] = {
                l.id: l for l in db.query(Locality).all()
            }

            iterator = ET.iterparse(file)
            for _, element in iterator:
                element.tag = element.tag.removeprefix("{http://www.naptan.org.uk/}")
                if element.tag == "Regions":
                    log.debug("Importing regions")
                    for item in handle_region(element):
                        if type(item) is Region:
                            if item.id not in regions.keys():
                                db.add(item)
                            elif regions[item.id].modified_at != item.modified_at:
                                db.merge(item)

                        if type(item) is AdminArea:
                            if item.id not in admin_areas.keys():
                                db.add(item)
                            elif admin_areas[item.id].modified_at != item.modified_at:
                                db.merge(item)

                        if type(item) is District:
                            if item.id not in districts.keys():
                                db.add(item)
                            elif districts[item.id].modified_at != item.modified_at:
                                db.merge(item)
                    element.clear()

                elif element.tag == "NptgLocalities":
                    log.debug("Importing localities")
                    l_with_parents = []
                    for item in handle_locality(element):
                        if item.parent_id and item.parent_id not in localities.keys():
                            l_with_parents.append(item)
                        else:
                            if item.id not in localities.keys():
                                db.add(item)
                            elif localities[item.id].modified_at != item.modified_at:
                                db.merge(item)
                            localities[item.id] = item

                    element.clear()
                    for locality in l_with_parents:
                        if locality.parent_id in localities.keys():
                            db.merge(locality)

                    for locality in l_with_parents:
                        if locality.parent_id not in localities.keys():
                            db.add(locality)
            log.debug("Committing...")
            db.commit()
            log.debug("Import complete")
            log.debug("Syncing search vectors")
            with engine.begin() as conn:
                sync_trigger(
                    conn,
                    "locality",
                    "search_vector",
                    [
                        "name",
                        "qualifier_name",
                    ],
                )
        except Exception as e:
            log.debug(f"Error during import: {e}")
            db.rollback()


def main():
    setup_logging()
    url = "https://naptan.api.dft.gov.uk/v1/nptg"

    log.debug(f"Downloading NPTG data from {url}...")
    nptg_path = download_to_static(url, "NPTG.xml")
    if not nptg_path:
        log.debug("Failed to download NPTG data.")
        sys.exit(1)
    try:
        import_nptg_data()
    except KeyboardInterrupt:
        log.debug("Stopped by user.")
    finally:
        nptg_path.unlink()


if __name__ == "__main__":
    main()
