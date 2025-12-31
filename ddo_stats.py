labels = {
    "melee_power": "Melee Power:  ",
    "doublestrike": "Doublestrike: ",
    "mainhand_damage_ability_multiplier": "Mainhand damage ability multiplier: ",
    "helpless_damage_bonus": "Helpless Damage bonus: "
}

def get_stat(ddo_file: list, label_string: str) -> int:
    """The DDO builder by Maetrim exports a text file. Convert it to a list of strings, where every row in the text file is a new element in the list. Pass the
    label of the stat you want as well, for instance, 'Melee Power:   '. Be careful to copy these labels from the build export, there are invisible character
    codes in the file."""

    extracted_int = 0

    for row in ddo_file:
        if isinstance(row, str) and row.startswith(label_string):
            strip_label = row.strip(label_string)
            strip_percentage = strip_label.strip("%")

            extracted_int = int(float(strip_percentage))

    return extracted_int


def get_expected_damage(ddo_file: list) -> float:
    """In DDO, the player rolls a D20 to damage. Because this is a Monte Carlo distribution, calculate the expected damage by adding all damage from 1 to 20 and
    then dividing this total by 20."""
    
    on_hit_label = "On Hit         "
    dice_multiplier = 0.0
    dice_average = 0
    damage_on_hit = 0
    damage_on_crit = 0
    crit_range_minus_19_20 = 0
    damage_on_19_20_crit = 0


    for row in ddo_file:
        if isinstance(row, str) and row.startswith(on_hit_label):
            strip_label = row.strip(on_hit_label)
            opening_bracket_id = strip_label.find("[")
            closing_bracket_id = strip_label.find("]")
            if opening_bracket_id != -1 and dice_multiplier == 0.0:
                # Check to see if dice_mulitiplier is zero to make only the Main Hand weapon gets calculated
                dice_multiplier_string = strip_label[:opening_bracket_id]
                dice_multiplier = float(dice_multiplier_string)
                dice_string = strip_label[(opening_bracket_id + 1):closing_bracket_id]
                # A dice string has the format 2d8+2, wich means: "roll two eight-sided dice and add 2"
                print(dice_string) # Log this
                d_id = dice_string.find("d")
                plus_sign_id = dice_string.find("+")
                number_of_dice = float(dice_string[:d_id])
                dice_size = float(dice_string[(d_id + 1):plus_sign_id])
                add_to_roll = float(dice_string[(plus_sign_id + 1):])
                dice_average = (number_of_dice + (number_of_dice * dice_size)) / 2 + add_to_roll


    return dice_average
