def pytest_itemcollected(item):
    marker = item.get_closest_marker("description")
    if marker:
        item._nodeid = f"{item._nodeid} - {marker.args[0]}"
