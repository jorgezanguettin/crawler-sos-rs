import scrapy
import json

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
        "Casa, Mesa e Banho",
        None
    ]
    array_situation = [
        "Precisando de Ajuda",
        "Indeterminado",
        None
    ]
    array_characteristics = [
        "Sem Água",
        "Sem Eletricidade",
        "Sem Comida",
        "Ferido",
        "Mobilidade Limitada",
        "Grávida",
        "Necessidades Especiais",
        "Idoso",
        "Criança",
        "Recém-Nascido",
        "Sem Medicamentos",
        "Animais",
        "Sem Bateria De Celular",
        None
    ]

    def start_requests(self):
        for status in self.array_status:
            for situation in self.array_situation:
                for characteristic in self.array_characteristics:
                    filters = self.parse_filters(status, situation, characteristic)
                    yield from self.request_ajuders(filters, situation)

    def request_ajuders(self, filters, situation):
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
                    "filters": filters,
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

    
    def parse_filters(self, status, situation, characteristic):
        filter = f'(ImageT:"true" OR ImageT:"false") AND (EnderecoT:"true" OR EnderecoT:"false") AND (TelefoneT:"true" OR TelefoneT:"false")'

        if status:
            filter += f' AND (Status:"{status}")'
        if situation:
            filter += f' AND (StatusSituation:"{situation}")'
        if characteristic:
            filter += f' AND (Characteristics:"{characteristic}")'

        return filter
    
        
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