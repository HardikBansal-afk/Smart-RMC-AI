def validate_rows(rows):

    unique = {}

    for row in rows:

        key = row["item"].lower()

        if key not in unique:

            unique[key] = row

    return list(
        unique.values()
    )