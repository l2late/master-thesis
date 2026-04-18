from alphabuilding.domain.entities import PhysicalQuantity


def test_name_has_no_leading_nor_trailing_whitespaces():
    name = " Temperature "
    unit = "Celsius"
    pq = PhysicalQuantity(name=name, unit=unit)
    assert pq.name == "Temperature", (
        "PhysicalQuantity name should not have trailing whitespaces"
    )


def test_unit_has_no_leading_nor_trailing_whitespaces():
    name = "Temperature "
    unit = " Celsius "
    pq = PhysicalQuantity(name=name, unit=unit)
    assert pq.unit == "Celsius", (
        "PhysicalQuantity unit should not have trailing whitespaces"
    )
