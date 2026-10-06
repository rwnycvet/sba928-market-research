"""Calculate evidence rules used in market-research reports."""


def customer_count_warning(identified_customers):
    """Return True when fewer than five customers are identified."""

    # Reject missing values, text, decimals and Boolean values.
    if type(identified_customers) is not int:
        raise TypeError(
            "Identified customer count must be a whole-number integer."
        )

    if identified_customers < 0:
        raise ValueError(
            "Identified customer count cannot be negative."
        )

    return identified_customers < 5


def repeat_customer_percentage(identified_customers, repeat_customers):
    """Calculate repeat purchasing among customers with recorded IDs."""

    for name, value in (
        ("identified_customers", identified_customers),
        ("repeat_customers", repeat_customers),
    ):
        if type(value) is not int:
            raise TypeError(f"{name} must be a whole-number integer.")

        if value < 0:
            raise ValueError(f"{name} cannot be negative.")

    if repeat_customers > identified_customers:
        raise ValueError(
            "Repeat customers cannot exceed identified customers."
        )

    if identified_customers == 0:
        return None  # No identified customers means no defined percentage.

    return round(repeat_customers / identified_customers * 100, 2)


def main():
    for count in (3, 4, 5, 8):
        warning = customer_count_warning(count)
        decision = "Yes" if warning else "No"

        print(f"Identified customers: {count} | Warning applies: {decision}")


if __name__ == "__main__":
    main()