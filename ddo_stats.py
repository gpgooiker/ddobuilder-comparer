def melee_power(ddo_file: list) -> int:
    label_string = 'Melee Power:  '
    extracted_int = 0

    for row in ddo_file:
        if isinstance(row, str) and row.startswith(label_string):
            stripped_string = row.strip(label_string)
            extracted_int = int(float(stripped_string))

    return extracted_int