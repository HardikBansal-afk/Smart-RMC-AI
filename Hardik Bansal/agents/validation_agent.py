def run(rows):

    unique = {}

    for row in rows:

        item = row["item"].lower()

        if item not in unique:

            unique[item] = row

    return list(
        unique.values()
    )