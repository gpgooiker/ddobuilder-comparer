def get_stat(ddo_file: list, label_string: str) -> int:

    extracted_int = 0

    for row in ddo_file:
        if isinstance(row, str) and row.startswith(label_string):
            strip_label = row.strip(label_string)
            strip_percentage = strip_label.strip("%")

            extracted_int = int(float(strip_percentage))

    return extracted_int

labels = {
    "melee_power": "Melee Power:  ",
    "doublestrike": "Doublestrike: ",
    "mainhand_damage_ability_multiplier": "Mainhand damage ability multiplier: ",
    "helpless_damage_bonus": "Helpless Damage bonus: "
}

