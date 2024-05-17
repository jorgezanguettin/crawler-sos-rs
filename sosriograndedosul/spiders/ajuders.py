import json
import scrapy


class AjudeRSSpider(scrapy.Spider):
    name = "ajuders"

    array_status = [
        "Desaparecido",
        "Ilhado",
        "Abrigado",
        "Resgate",
        "Alimento",
        "Água",
        "Medicamento",
        "Higiene e Produtos de Limpeza",
        "Roupas ou cobertas",
        "Ajuda de Voluntários",
        "Casa",
        "Mesa e Banho",
    ]
    array_situation = [
        "Precisando de Ajuda",
        "Indeterminado",
    ]

    def start_requests(self):
        for status in self.array_status:
            for situation in self.array_situation:
                yield from self.request_ajuders(status, situation)

    def request_ajuders(self, status, situation):
        yield scrapy.Request(
            method="POST",
            url="https://ilxunwwlgr-1.algolianet.com/1/indexes/LiveReports/query?x-algolia-agent=Algolia%20for%20JavaScript%20(4.22.1)%3B%20Browser",
            body=json.dumps(
                {
                    "query": "",
                    "page": 0,
                    "hitsPerPage": 999,
                    "attributesToRetrieve": ["uniqueid"],
                    "sortFacetValuesBy": "count",
                    "filters": f'(Status:"{status}") AND (StatusSituation:"{situation}") AND (ImageT:"true" OR ImageT:"false") AND (EnderecoT:"true" OR EnderecoT:"false") AND (TelefoneT:"true" OR TelefoneT:"false")',
                    "optionalFilters": "",
                }
            ),
            headers={
                "x-algolia-application-id": "ILXUNWWLGR",
                "x-algolia-api-key": "673c9fb9403cfbab6c423dbfd2899902",
            },
            callback=self.parse_ajuders,
            meta={"situation": situation},
        )

    def parse_ajuders(self, response):
        data = response.json()

        for helped_raw in data["hits"]:
            helped_details = helped_raw["_highlightResult"]

            helped = {
                "uniqueid": helped_raw["uniqueid"],
                "objectID": helped_raw["objectID"],
                "latitude": "",
                "longitude": "",
                "characteristics": "",
                "cpf": "",
                "description": "",
                "locationtext": "",
                "situation": response.meta["situation"],
                "status": "",
                "telefone": "",
                "title": "",
            }

            for k, v in sorted(helped_details.items()):
                key = str(k).lower().strip()

                if key == "_geoloc":
                    geoloc = helped_details["_geoloc"]

                    helped["latitude"] = geoloc.get("lat", {}).get("value")
                    helped["longitude"] = geoloc.get("lng", {}).get("value")
                elif key == "characteristics":
                    helped["characteristics"] = ";".join(
                        [value.get("value") for value in v]
                    )
                else:
                    if key in helped.keys():
                        helped[key] = v.get("value")

            yield helped
