import pytest
from .tally import Period


@pytest.mark.parametrize(
    "name,window,window2,target,result",  # type: ignore
    [
        ("Weekly", 7, 20, 365, 7),
        ("Weekly - prorated", 7, 3, 365, 3),
        ("Weekly - floor", 7, 20, 120, 2),
    ],
)
def test_weekly_target(
    name: str, window: int, window2: int, target: int, result: int
) -> None:
    assert Period(name, window).target(window2, target) == result
