import logging
logger = logging.getLogger(__name__)

labels = {
    "melee_power": "Melee Power:",
    "doublestrike": "Doublestrike:",
    "mainhand_damage_ability_multiplier": "Mainhand damage ability multiplier:",
    "helpless_damage_bonus": "Helpless Damage bonus:",
    "hit_points": "HP:",
    "prr": "PRR:",
    "mrr": "MRR:",
    "dodge": "Dodge:",
    "armor_class": "AC:",
    "sneak_attack_damage": "Sneak Attack Damage: "
}


def get_stat(ddo_file: list, label_string: str) -> float:
    """The DDO builder by Maetrim exports a text file. Convert it to a list of strings, where every row in the text file is a new element in the list. Pass the
    label of the stat you want as well, for instance, 'Melee Power:'. Be careful to copy these labels from the build export, there are invisible character
    codes in the file.
    
    Example block from a build file:
        Extract the defensive stats from this block in a ddo build file:
                 Start Tome Final      HP:       6408      Displacement:   50%
        Str:    10    8    42      Unc Rng:  -153      Incorp:          0%
        Dex:     8    8    30      PRR:       384      AC:             185
        Con:    18    8   103      MRR:       210      +Healing Amp:   146
        Int:    10    8    24      Dodge:   16/27      -Healing Amp:    10
        Wis:    10    8    30      Fort:     345%      Repair Amp:      10
    """

    extracted_float = float(0)

    for row in ddo_file:
        if isinstance(row, str) and label_string in row:
            end_of_label_id = row.find(label_string) + len(label_string)
            stripped_to_end_of_label = row[end_of_label_id:]
            # Often, the ddo build files sport one or more spaces
            stripped_up_to_stat = stripped_to_end_of_label.strip()

            extracted_float = float(_get_stat_from_the_start_of_a_string(stripped_up_to_stat))

            logger.debug(f'Extracted {label_string} {extracted_float}.')
            return extracted_float

    logger.debug(f'Extracted {label_string} {extracted_float}.')
    return extracted_float


def _get_stat_from_the_start_of_a_string(string_starting_with_stat: str) -> int:
    stat_as_array = []

    for character in string_starting_with_stat:
        if character.isdigit():
            stat_as_array.append(character)
        else:
            # Stop if there's a % sign or a series of spaces
            return int(''.join(stat_as_array))

    return int(''.join(stat_as_array))
