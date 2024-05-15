import os
import gspread

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


class GSpreadMethods:
    def __init__(self) -> None:
        gc = gspread.service_account(filename=f"{ROOT_DIR}/api_credentials.json")

        spreadsheet_id = "1xRt5dn4d4L-aBBNdKGvGjN3u0q9N0QDl65Y3AzJLaVE"
        spreadsheet = gc.open_by_key(spreadsheet_id)
        self.shelters = spreadsheet.worksheet("Shelters")
        self.shelters_supplies = spreadsheet.worksheet("Shelters Supplies")


class SosriograndedosulPipeline(GSpreadMethods):
    shelters_rows = []
    shelters_supplies_rows = []

    def close_spider(self, spider):
        self.shelters.batch_clear(["A2:Z5000"])
        self.shelters_supplies.batch_clear(["A2:Z5000"])

        self.shelters.batch_update(
            [{"range": "A2:Z5000", "values": self.shelters_rows}]
        )
        self.shelters_supplies.batch_update(
            [{"range": "A2:Z5000", "values": self.shelters_supplies_rows}]
        )

    def process_item(self, item, spider):
        shelter_supplies_raw = item["shelterSupplies"].copy()
        del item["shelterSupplies"]

        for shelter_supplies in shelter_supplies_raw:
            shelter_supplies["tags"] = ", ".join(shelter_supplies["tags"])
            for k, v in sorted(shelter_supplies["supply"].items()):
                shelter_supplies[f"supply_{k}"] = v
            del shelter_supplies["supply"]

            self.shelters_supplies_rows.append(self.process_dict_rows(shelter_supplies))

        self.shelters_rows.append(self.process_dict_rows(item))

        return item

    def process_dict_rows(self, item):
        row = []

        for k, v in sorted(item.items()):
            row.append(v)

        return row
