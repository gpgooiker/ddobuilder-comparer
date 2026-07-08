import logging
from ddo_file_parser import get_stat, labels
logger = logging.getLogger(__name__)

def get_average_sneak_attack_damage(ddo_file: list) -> float:
    """Extract the average sneak attack damage from a ddo build file. The average is calculated by taking the average of the dice rolled and adding any bonus damage.
    Example block from a build file:
        Sneak Attack Damage: 2d6+3"""

    average_sneak_attack_damage = float(0)
    for row in ddo_file:
        if isinstance(row, str) and row.startswith(labels["sneak_attack_damage"]):
            logger.debug(f'Found the sneak attack damage row: {row}.')
            stripped_to_end_of_label = row[len(labels["sneak_attack_damage"]):]
            stripped_up_to_stat = stripped_to_end_of_label.strip()

            if _is_a_dice_string(stripped_up_to_stat):
                average_sneak_attack_damage = _calculate_average_damage_from_dice_string(stripped_up_to_stat)
                logger.debug(f'Calculated the average sneak attack damage: {average_sneak_attack_damage}.')
                return average_sneak_attack_damage

    return average_sneak_attack_damage

def get_expected_damage(ddo_file: list) -> float:
    """In DDO, the player rolls a D20 to damage. Calculate the expected damage from one hit by adding all damage
    from 1 to 20 and then dividing this total by 20.

    We get the expected damage from one hit from this block in the build file:
        Main Hand: Ignition, the Fear and Flame
        On Hit         5.65[1d10+3]+128
        Critical 17-18 (5.65[1d10+3]+139) * 2
        Critical 19-20 (5.65[1d10+3]+139) * 2
    
    We add the sneak attack damage to the expected damage too. TODO: weigh the sneak attack damage by the chance
    of a sneak attack happening, which depends on some circumstances."""

    dice_multiplier, dice_average, average_damage_on_hit = _parse_normal_hit(ddo_file)
    crit_range, average_damage_on_crit = _parse_normal_crit(ddo_file, dice_multiplier, dice_average)
    average_damage_on_crit19_20 = _parse_big_crit(ddo_file, dice_multiplier, dice_average)
    average_sneak_attack_damage = get_average_sneak_attack_damage(ddo_file)

    crit_range_on_19_20 = 2.0  # 19 or 20
    hit_range = 20.0 - crit_range - crit_range_on_19_20
    logger.debug(f'Normal hit range: {hit_range}, crit range: {crit_range}, 19-20 crit range: {crit_range_on_19_20}')

    expected_damage = ((average_damage_on_hit * hit_range) +
                       (average_damage_on_crit * crit_range) +
                       (average_damage_on_crit19_20 * crit_range_on_19_20)
                       ) / 20
    logger.debug(f'Calculated the expected damage by averaging all die rolls from 1 - 20: {expected_damage}. Added sneak dice.')
    return expected_damage + average_sneak_attack_damage

def convert_to_factor(number: float) -> float:
    return (number + 100) / 100

def reduction_rating_to_percentage(rr: float) -> float:
    """DDO has stats called MRR and PRR. These convert to percentages with this formula: https://ddowiki.com/page/Physical_Resistance_Rating#Formula."""
    return 1 - (100.0 / (100.0 + rr))

def normalize_dodge(dodge: float) -> float:
    """To compare stats that work differently and have a different range, we normalize them so they're a number between 0 and 1. https://en.wikipedia.org/wiki/Feature_scaling"""
    min_value = 6
    max_value = 50

    return (dodge - min_value) / (max_value - min_value)

def normalize_armor_class(armor_class: float) -> float:
    min_value = 30.0
    max_value = 400.0

    return (armor_class - min_value) / (max_value - min_value)

def _parse_normal_hit(ddo_file: list) -> tuple[float, float, float]:
    """Parse the first 'On Hit' line (main hand weapon) and return
    (dice_multiplier, dice_average, average_damage_on_hit).

    Parses lines like: On Hit         5.65[1d10+3]+128
    """
    on_hit_label = "On Hit         "
    try:
        for row in ddo_file:
            if not (isinstance(row, str) and row.startswith(on_hit_label)):
                continue
            body = row[len(on_hit_label):]
            if not ("[" in body and "]" in body and "+" in body):
                continue

            opening_bracket = body.find("[")
            closing_bracket = body.find("]")
            dice_multiplier = float(body[:opening_bracket])

            dice_string = body[opening_bracket + 1:closing_bracket]
            dice_average = 0.0
            if _is_a_dice_string(dice_string):
                logger.debug(f'Extracted the dice string: {dice_string}.')
                dice_average = _calculate_average_damage_from_dice_string(dice_string)
                logger.debug(f'Calculated the average damage from the dice ({dice_average}), without bonus damage.')

            plus_damage_on_hit = float(row[row.rfind("+") + 1:])
            average_damage_on_hit = (dice_multiplier * dice_average) + plus_damage_on_hit
            logger.debug(f'Average damage on hit: {average_damage_on_hit}.')
            return dice_multiplier, dice_average, average_damage_on_hit
    except (ValueError, IndexError):
        logger.exception("Exception when parsing the normal hit line")
    return 0.0, 0.0, 0.0


def _parse_normal_crit(ddo_file: list, dice_multiplier: float, dice_average: float) -> tuple[float, float]:
    """Parse the first non-19-20 'Critical' line and return (crit_range, average_damage_on_crit).

    Parses lines like: Critical 17-18 (5.65[1d10+3]+139) * 2
    """
    try:
        for row in ddo_file:
            if not (isinstance(row, str) and row.startswith("Critical ") and "19-20" not in row):
                continue
            plus_damage_on_crit = float(row[:row.find(")")][row.rfind("+") + 1:])
            logger.debug(f'Extracted the bonus damage on crits: {plus_damage_on_crit}.')
            crit_multiplier = float(row[row.rfind("* ") + 1:])
            logger.debug(f'Extracted the crit multiplier: {crit_multiplier}.')
            crit_range_string = row[row.find(" ") + 1:row.find("(")]
            crit_range = _calculate_crit_range_from_string(crit_range_string)
            logger.debug(f'Calculated the crit range: {crit_range}.')
            average_damage_on_crit = _calculate_crit_damage(dice_multiplier, dice_average, plus_damage_on_crit, crit_multiplier)
            logger.debug(f'Calculated average crit damage: {average_damage_on_crit}.')
            return crit_range, average_damage_on_crit
    except (ValueError, IndexError):
        logger.exception("Exception when parsing the normal crit line")
    return 0.0, 0.0


def _parse_big_crit(ddo_file: list, dice_multiplier: float, dice_average: float) -> float:
    """Parse the 'Critical 19-20' line and return average_damage_on_crit19_20.

    Parses lines like: Critical 19-20 (5.65[1d10+3]+139) * 2
    """
    try:
        for row in ddo_file:
            if not (isinstance(row, str) and row.startswith("Critical ") and "19-20" in row):
                continue
            plus_damage_on_crit = float(row[:row.find(")")][row.rfind("+") + 1:])
            crit_multiplier = float(row[row.rfind("* ") + 1:])
            logger.debug(f'Extracted the crit multiplier for 19-20 crits: {crit_multiplier}.')
            average_damage = _calculate_crit_damage(dice_multiplier, dice_average, plus_damage_on_crit, crit_multiplier)
            logger.debug(f'Calculated average damage for 19-20 crits: {average_damage}.')
            return average_damage
    except (ValueError, IndexError):
        logger.exception("Exception when parsing the 19-20 crit line")
    return 0.0


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

def compute_offensive_score(ddo_file: list) -> float:
    """Calculate an offensive fitness score for the main hand weapon.
    Factors in expected damage per roll, melee power, doublestrike, and helpless damage bonus."""
    melee_power = get_stat(ddo_file, labels["melee_power"])
    doublestrike = get_stat(ddo_file, labels["doublestrike"])
    helpless_damage_bonus = get_stat(ddo_file, labels["helpless_damage_bonus"])
    expected_damage = get_expected_damage(ddo_file)

    return (expected_damage *
            convert_to_factor(melee_power) *
            convert_to_factor(doublestrike) *
            convert_to_factor(helpless_damage_bonus))

def compute_defensive_score(ddo_file: list) -> float:
    """Calculate a defensive fitness score approximating 'Effective Hit Points'.
    Factors in HP, physical and magical damage reduction, dodge, and armor class."""
    hit_points = get_stat(ddo_file, labels["hit_points"])
    prr_percentage = reduction_rating_to_percentage(get_stat(ddo_file, labels["prr"]))
    logger.debug(f"The physical damage percentage that's reduced by PRR: {prr_percentage}.")
    mrr_percentage = reduction_rating_to_percentage(get_stat(ddo_file, labels["mrr"]))
    logger.debug(f"The elemental damage percentage that's reduced by MRR: {mrr_percentage}.")
    dodge = get_stat(ddo_file, labels["dodge"])
    armor_class = get_stat(ddo_file, labels["armor_class"])
    return (hit_points *
            (1.0 + prr_percentage) *
            (1.0 + mrr_percentage) *
            (1.0 + normalize_dodge(dodge)) *
            (1.0 + normalize_armor_class(armor_class)))
