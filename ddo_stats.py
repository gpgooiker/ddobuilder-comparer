import logging
from ddo_file_parser import get_stat
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
    "armor_class": "AC:"
}

def get_expected_damage(ddo_file: list) -> float:
    """In DDO, the player rolls a D20 to damage. Calculate the expected damage from one hit by adding all damage
    from 1 to 20 and then dividing this total by 20.

    We get the expected damage from one hit from this block in the build file:
        Main Hand: Ignition, the Fear and Flame
        On Hit         5.65[1d10+3]+128
        Critical 17-18 (5.65[1d10+3]+139) * 2
        Critical 19-20 (5.65[1d10+3]+139) * 2"""

    average_damage_on_hit_calculated = False
    on_hit_label = "On Hit         "
    dice_multiplier = 0.0
    dice_average = 0.0
    average_damage_on_hit = 0.0
    hit_range = 0.0

    crit_damage_calculated = False
    crit_range = 0.0
    average_damage_on_crit = 0.0

    crit_damage_on_19_20_calculated = False
    crit_range_on_19_20 = 2.0 # 19 or 20!
    average_damage_on_crit19_20 = 0.0

    try:
        for row in ddo_file:
            if isinstance(row, str) and row.startswith(on_hit_label):
                strip_label = row.strip(on_hit_label)
                if "[" in row and "]" in row and "+" in row and average_damage_on_hit_calculated == False:
                    opening_bracket_id = strip_label.find("[")
                    closing_bracket_id = strip_label.find("]")

                    dice_multiplier_string = strip_label[:opening_bracket_id]
                    dice_multiplier = float(dice_multiplier_string)

                    dice_string = strip_label[(opening_bracket_id + 1):closing_bracket_id]
                    if _is_a_dice_string(dice_string):
                        logger.debug(f'Extracted the dice string: {dice_string}.')
                        dice_average = _calculate_average_damage_from_dice_string(dice_string)
                        logger.debug(f'Calculated the average damage from the dice ({dice_average}), without bonus damage.')

                    last_plus_sign_id = row.rfind("+")
                    plus_damage_on_hit = float(row[(last_plus_sign_id + 1):])
                    average_damage_on_hit = (dice_multiplier * dice_average) + plus_damage_on_hit
                    logger.debug(f'Average damage on hit: {average_damage_on_hit}.')


                    # Guard that only the Main Hand weapon gets calculated
                    average_damage_on_hit_calculated = True
    except:
        logger.exception("Exception when extracting the average damage from non-critical hits")

    try:
        """Extracting the info out of this bit: 'Critical 17-18 (5.65[1d10+3]+139) * 2'"""
        for row in ddo_file:
            if isinstance(row, str) and row.startswith("Critical "):
                last_plus_sign_id = row.rfind("+")
                plus_damage_on_crit_with_multiplier = row[:row.find(")")]
                plus_damage_on_crit_stripped = plus_damage_on_crit_with_multiplier[(last_plus_sign_id + 1):]
                plus_damage_on_crit = float(plus_damage_on_crit_stripped)

                if ("19-20" in row) is False and crit_damage_calculated is False:
                    crit_multiplier = 0.0

                    logger.debug(f'Extracted the bonus damage on all crits, those on 19 or 20 as well: {plus_damage_on_crit}.')
                    crit_multiplier = float(row[(row.rfind("* ") + 1):])
                    logger.debug(f'Extracted the crit modifier of ordinary crits on the first weapon in the file: {crit_multiplier}.')
                    crit_range_string = row[(row.find(" ") + 1):row.find("(")]
                    crit_range = _calculate_crit_range_from_string(crit_range_string)
                    logger.debug(f'Calculated the crit range of ordinary crits: {crit_range}.')
                    average_damage_on_crit = _calculate_crit_damage(dice_multiplier, dice_average, plus_damage_on_crit, crit_multiplier)
                    logger.debug(f'Calculated the average damage of a normal, non 19/20 crit: {average_damage_on_crit}.')
                    crit_damage_calculated = True
                elif crit_damage_on_19_20_calculated is False:
                    crit_multiplier_on_19_20 = float(row[(row.rfind("* ") + 1):])
                    logger.debug(f'Extracted the crit multiplier of big crits on 19 or 20: {crit_multiplier_on_19_20}.')
                    average_damage_on_crit19_20 = _calculate_crit_damage(dice_multiplier, dice_average, plus_damage_on_crit, crit_multiplier_on_19_20)
                    logger.debug(f'Calculated the average damage of big crits on 19 or 20: {average_damage_on_crit19_20}.')
                    crit_damage_on_19_20_calculated = True
    except:
        logger.exception("Exception when calculating the average damage from normal crits and crits on 19 or 20")

    hit_range = 20.0 - crit_range - crit_range_on_19_20
    logger.debug(f'Now we know the crit ranges of crits and big crits, we calculated the normal hit range: {hit_range}')

    expected_damage = ((average_damage_on_hit * hit_range) +
                        (average_damage_on_crit * crit_range) +
                        (average_damage_on_crit19_20 * crit_range_on_19_20)
                        ) / 20
    logger.debug(f'Calculated the expected damage by averaging all die rolls from 1 - 20: {expected_damage}.')
    return expected_damage

def convert_to_factor(number: float) -> float:
    return (number + 100) / 100

def reduction_rating_to_percentage(rr: float) -> float:
    """DDO has stats called MRR and PRR. These convert to percentages with this formula: https://ddowiki.com/page/Physical_Resistance_Rating#Formula."""
    return 1 - (100.0 / (100.0 + rr))

def normalize_dodge(dodge: float) -> float:
    """To compare stats that work differently and have a different range, we normalize them so they're a number between 0 and 1. https://en.wikipedia.org/wiki/Feature_scaling"""
    min = 6
    max = 50

    return (dodge - min) / (max - min)

def normalize_armor_class(armor_class: float) -> float:
    min = 30.0
    max = 400.0

    return (armor_class - min) / (max - min)

def _is_a_dice_string(dice_string: str) -> bool:
    """A dice string has the format 2d8+2, wich means: 'roll two eight-sided dice and add 2'"""

    return "d" in dice_string

def _calculate_average_damage_from_dice_string(dice_string: str) -> float:
    d_id = dice_string.find("d")
    plus_sign_id = dice_string.find("+")
    number_of_dice = float(dice_string[:d_id])
    dice_size = float(dice_string[(d_id + 1):plus_sign_id])
    add_to_roll = float(dice_string[(plus_sign_id + 1):])

    return (number_of_dice + (number_of_dice * dice_size)) / 2 + add_to_roll

def _calculate_crit_range_from_string(crit_range_string: str) -> float:
    if "-" in crit_range_string:
        dash_id = crit_range_string.find("-")
        start_range_on = float(crit_range_string[:dash_id])
        end_of_range = float(crit_range_string[(dash_id + 1):])

        return (end_of_range - start_range_on) + 1 # Count the first position as well
    else:
        return 0.0

def _calculate_crit_damage(dice_multiplier: float, dice_average: float, plus_damage_on_crit: float, crit_multiplier: float) -> float:
    return ((dice_multiplier * dice_average) + plus_damage_on_crit) * crit_multiplier
