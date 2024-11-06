import json
import re
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

from constants import BASE_URL, FOOD_DATA_BASE_URL, NAME_AND_DESCRIPTION_PATTERN, FILE_PATH


def collect_food_data(food_id: str) -> Dict[str, str | float] | None:
    def __convert_string_to_float(value: str):
        try:
            return float(value.replace(",", ".").strip())
        except ValueError:
            return 0.0

    print(f"Extracting food data from {food_id}...")

    food_data = {}
    portions = []

    response = requests.get(f"{FOOD_DATA_BASE_URL}?cod_produto={food_id}")

    soup = BeautifulSoup(response.content, 'html.parser')

    description_element = soup.find("h5", {"id": "overview"})

    if not description_element:
        return

    description_text = description_element.text

    if not (match := re.search(NAME_AND_DESCRIPTION_PATTERN, description_text)):
        return

    food_data["name"] = match.group("name").strip()

    description = match.group("description").strip()

    if description.endswith(","):
        description = description[:-1]

    food_data["description"] = description

    table = soup.find("table")

    if not table:
        return

    thead = table.find("thead")
    tbody = table.find("tbody")

    if not thead or not tbody:
        return

    headers = thead.find_all("th")[3:]

    for header in headers:
        portions.append({"name": header.text})

    rows = tbody.find_all("tr")

    # FIXME: I am not proud of that
    for index, row in enumerate(rows):
        if index == 1:  # Calories
            tds = row.find_all("td")[2:]
            food_data["kcal"] = __convert_string_to_float(tds[0].text)
            for i, td in enumerate(tds[1:]):
                portions[i]["kcal"] = __convert_string_to_float(td.text)
        elif index == 3:  # Carbohydrates
            tds = row.find_all("td")[2:]
            food_data["carbohydrates"] = __convert_string_to_float(tds[0].text)
            for i, td in enumerate(tds[1:]):
                portions[i]["carbohydrates"] = __convert_string_to_float(td.text)
        elif index == 5:  # Protein
            tds = row.find_all("td")[2:]
            food_data["protein"] = __convert_string_to_float(tds[0].text)
            for i, td in enumerate(tds[1:]):
                portions[i]["protein"] = __convert_string_to_float(td.text)
        elif index == 6:  # Lipids
            tds = row.find_all("td")[2:]
            food_data["lipids"] = __convert_string_to_float(tds[0].text)
            for i, td in enumerate(tds[1:]):
                portions[i]["lipids"] = __convert_string_to_float(td.text)
    
    food_data["portions"] = portions

    return food_data


def get_food_ids(page: int) -> List[str]:
    print(f"Extracting food IDs from page {page}...")

    food_ids = []

    response = requests.get(BASE_URL, params={"pagina": page})

    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.content, "html.parser")

    tbody = soup.find("tbody")

    if not tbody:
        return []

    tr_elements = tbody.find_all("tr")

    if not tr_elements:
        return []

    for tr in tr_elements:
        food_ids.append(tr.find_all("td")[0].text)

    return food_ids


def main():
    food_ids = []
    page = 1

    while (current_page_ids := get_food_ids(page)):
        food_ids.extend(current_page_ids)
        page += 1

    print(food_ids)
    print("Número de IDs:", len(food_ids))

    foods = []

    for food_id in food_ids:
        # FIXME: I am not proud of that
        try:
            food_data = collect_food_data(food_id)
        except:
            try:
                food_data = collect_food_data(food_id)
            except:
                food_data = None
        if food_data:
            foods.append(food_data)
    
    with open(FILE_PATH, "w") as file:
        json.dump(foods, file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
    # print(collect_food_data("BRC0923F"))
