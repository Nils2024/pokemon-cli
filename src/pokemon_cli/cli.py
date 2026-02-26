import csv
from pathlib import Path
from shlex import join
from typing import List

import requests

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from urllib3.util import url

app = typer.Typer(help="Mein cooles CLI Tool")
console = Console()

def getGermanName(name : str):
    gerName : str = ""

    csv_path = Path(__file__).parent / "pokemon_species_names.csv"
    with open(csv_path, newline='', encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)
        for row in reader:
            rowNum = int(row[1])
            if rowNum == 6:
                gerName = row[2]
            if rowNum == 7:
                engName = row[2]
                if name.lower() == gerName.lower():
                    return engName.lower()


@app.command()
def name(
        name: str = typer.Argument(..., help="Name of Pokemon.",),
):
    typeList = []
    typeUrlList = []
    engName : str = getGermanName(name)

    if not engName:
        console.print("[red]Pokemon nicht gefunden![/red]")
        return

    response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{engName}")
    if response.status_code == 200:
        data = response.json()
        for entry in data["types"]:
            type_name = entry["type"]["name"]
            type_url = entry["type"]["url"]
            typeUrlList.append(type_url)
            typeList.append(type_name)

    else:
        console.print("[red]Pokemon not found :(")
        return


    typeTable = Table(title="Typ:")
    typeTable.add_column("Typ", style="cyan")
    for entry in typeList:
        typeTable.add_row(entry)
    console.print(typeTable)


    if len(typeList) > 1:
        getDamageRelations(typeUrlList[0], typeUrlList[1])
    else:
        getDamageRelations(typeUrlList[0])



def getDamageRelations(url : str, url2 : str | None = None ):
    quadruple_damageList = []
    double_damageList = []
    normal_damageList = []
    half_damageList = []
    quarter_damageList = []
    no_damageList = []

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        relations = data["damage_relations"]
        for entry in relations["double_damage_from"]:
            double_damageList.append(entry["name"])
        for entry in relations["half_damage_from"]:
            half_damageList.append(entry["name"])
        for entry in relations["no_damage_from"]:
            no_damageList.append(entry["name"])

    if url2 is not None:
        response2 = requests.get(url2)
        if response2.status_code == 200:
            data2 = response2.json()
            relations2 = data2["damage_relations"]
            for entry in relations2["double_damage_from"]:
                damage = entry["name"]
                if damage in double_damageList:
                    quadruple_damageList.append(damage)
                    double_damageList.remove(damage)
                elif damage in half_damageList:
                    half_damageList.remove(damage)
                    normal_damageList.append(damage)
                else:
                    double_damageList.append(damage)

            for entry in relations2["half_damage_from"]:
                damage = entry["name"]
                if damage in half_damageList:
                    quarter_damageList.append(damage)
                    half_damageList.remove(damage)
                elif damage in double_damageList:
                    double_damageList.remove(damage)
                    normal_damageList.append(damage)
                else:
                    half_damageList.append(damage)

            for entry in relations2["no_damage_from"]:
                damage = entry["name"]
                for lst in [quadruple_damageList, double_damageList, half_damageList, quarter_damageList]:
                    if damage in lst:
                        lst.remove(damage)
                if damage not in no_damageList:
                    no_damageList.append(damage)

    all_damage_list = {
        "4x":  quadruple_damageList,
        "2x": double_damageList,
        "1": normal_damageList,
        "0.5x": half_damageList,
        "0.25x": quarter_damageList,
        "0": no_damageList
    }

    table = Table(title="Schaden")
    table.add_column("Multiplikator", style="cyan")
    table.add_column("Typ", style="red")

    for multiplier, types in all_damage_list.items():
        if types:
            table.add_row(multiplier, ", " .join(types))
    console.print(table)

    return all_damage_list


def main():
    app()