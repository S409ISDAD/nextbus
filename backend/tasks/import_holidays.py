from govuk_bank_holidays.bank_holidays import BankHolidays
from sqlalchemy import and_
from backend.db.db import SessionLocal
from sqlalchemy.orm import Session
from backend.models import BankHoliday, BankHolidayDate


def get_bank_holiday_name(bank_holiday):
    title = bank_holiday["title"].replace("’", "").replace(" ", "")
    if bank_holiday["notes"] == "Substitute day":
        title += "Holiday"
    return title


def normalize_name(title: str) -> str:
    match title:
        case "EarlyMaybankholiday" | "EarlyMaybankholiday(VEday)":
            return "MayDay"
        case "Springbankholiday":
            return "SpringBank"
        case "Summerbankholiday":
            return "LateSummerBankHolidayNotScotland"
        case _:
            return title


def import_bank_holidays():
    bank_holidays = BankHolidays()

    with SessionLocal() as db:
        existing_bhs: dict[str, BankHoliday] = {
            str(bh.name): bh for bh in db.query(BankHoliday).all()
        }
        england_and_wales = bank_holidays.get_holidays(
            division=bank_holidays.ENGLAND_AND_WALES
        )

        for bank_holiday in england_and_wales:
            title = normalize_name(get_bank_holiday_name(bank_holiday))

            bh = existing_bhs[title]

            existing_date = (
                db.query(BankHolidayDate)
                .filter(
                    and_(
                        BankHolidayDate.bank_holiday_id == bh.id,
                        BankHolidayDate.date == bank_holiday["date"],
                    )
                )
                .first()
            )

            if not existing_date:
                db.add(BankHolidayDate(bank_holiday=bh, date=bank_holiday["date"]))

        db.commit()


if __name__ == "__main__":
    import_bank_holidays()
    print("✔ Bank holidays imported successfully")
