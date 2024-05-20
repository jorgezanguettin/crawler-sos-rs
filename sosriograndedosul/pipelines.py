import os
import re
import json
import gspread
import requests
from requests.adapters import HTTPAdapter, Retry

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


s = requests.Session()
retries = Retry(total=5, backoff_factor=1)
s.mount("https://", HTTPAdapter(max_retries=retries))


class GSpreadMethods:
    def __init__(self) -> None:
        gc = gspread.service_account(filename=f"{ROOT_DIR}/api_credentials.json")

        spreadsheet_id = "1xRt5dn4d4L-aBBNdKGvGjN3u0q9N0QDl65Y3AzJLaVE"
        spreadsheet = gc.open_by_key(spreadsheet_id)
        self.shelters = spreadsheet.worksheet("Abrigos-SOSRS")
        self.shelters_supplies = spreadsheet.worksheet("Suprimentos-SOSRS")
        self.helpeds = spreadsheet.worksheet("Ocorrencias-AJUDERS")


class SosriograndedosulPipeline(GSpreadMethods):
    functions = {}

    shelters_rows = []
    shelters_supplies_rows = []
    helpeds_rows = []

    coords = json.loads(open(f"{ROOT_DIR}/coords.json", "r", encoding="utf-8").read())

    def open_spider(self, spider):
        self.functions = {
            "sosrs": self.process_sosrs_item,
            "ajuders": self.process_ajuders_item,
        }

    def close_spider(self, spider):
        if spider.name == "sosrs":
            self.shelters.batch_clear(["A2:Z5000"])
            self.shelters_supplies.batch_clear(["A2:Z5000"])

            self.shelters.batch_update(
                [{"range": "A2:Z5000", "values": self.shelters_rows}]
            )
            self.shelters_supplies.batch_update(
                [{"range": "A2:Z5000", "values": self.shelters_supplies_rows}]
            )
        elif spider.name == "ajuders":
            self.dedup_helpeds_items()
            self.helpeds.batch_clear(["A2:Z5000"])
            self.helpeds.batch_update(
                [{"range": "A2:Z5000", "values": self.helpeds_rows}]
            )

    def process_item(self, item, spider):
        return self.functions[spider.name](item)

    def process_ajuders_item(self, item):
        self.helpeds_rows.append(self.process_dict_rows(item, "helpeds"))

        return item

    def process_sosrs_item(self, item):
        shelter_supplies_raw = item["shelterSupplies"].copy()
        del item["shelterSupplies"]

        for shelter_supplies in shelter_supplies_raw:
            shelter_supplies["tags"] = ", ".join(shelter_supplies["tags"])
            for k, v in sorted(shelter_supplies["supply"].items()):
                shelter_supplies[f"supply_{k}"] = v
            del shelter_supplies["supply"]

            self.shelters_supplies_rows.append(
                self.process_dict_rows(shelter_supplies, "shelterSupplies")
            )

        self.shelters_rows.append(self.process_dict_rows(item))

        return item

    def process_dict_rows(self, item, item_type="shelter"):
        row = []

        if item_type == "shelter":
            conditions = (not item["latitude"], not item["longitude"])
            if all(conditions):
                item = self.get_coords_by_postalcode(item)
            else:
                item["zipCode"] = (
                    item["zipCode"].replace("-", "") if item["zipCode"] else ""
                )

        for k, v in sorted(item.items()):
            row.append(v)

        return row

    def get_coords_by_postalcode(self, item):
        if not item["zipCode"]:
            zipcode_raw = "0"
        else:
            zipcode_raw = item["zipCode"].replace("'", "").strip()

        if int(zipcode_raw.replace("-", "")) == 0:
            zipcode = re.compile(r"[0-9]{5}[-]{0,1}[0-9]{3}").findall(item["address"])
        else:
            zipcode = item["zipCode"]

        if zipcode and isinstance(zipcode, list):
            zipcode = zipcode[0]

        if zipcode:
            coords_maps = self.get_coordinates(zipcode)

            item["zipCode"] = zipcode.replace("-", "")

            if coords_maps:
                item["latitude"] = str(coords_maps["latitude"]).replace(".", ",")
                item["longitude"] = str(coords_maps["longitude"]).replace(".", ",")
        else:
            item["zipCode"] = ""

        return item

    def get_coordinates(self, postal_code):
        base_url = "https://maps.googleapis.com/maps/api/geocode/json"

        params = {
            "address": postal_code,
            "key": os.getenv("GMAPS_APIKEY"),
        }

        if postal_code.replace("-", "") in self.coords:
            return self.coords[postal_code.replace("-", "")]

        response = s.get(base_url, params=params, timeout=60)

        if response.status_code == 200:
            data = response.json()
            if len(data["results"]) > 0:
                location = data["results"][0]["geometry"]["location"]
                latitude = location["lat"]
                longitude = location["lng"]

                return {"latitude": latitude, "longitude": longitude}
        return {"latitude": "", "longitude": ""}

    def dedup_helpeds_items(self):
        itemList = self.helpeds_rows

        dupList = []
        i = 0
        while i < len(itemList):
            if itemList[i][6] not in dupList:
                dupList.append(itemList[i][6])
                i += 1
            else:
                itemList.pop(i)