from helpers import add

# invoke by cd'ing into the vintage_car_exploration repo and running
# pytest -v


def test_add():
    assert add(1, 1) == 2
