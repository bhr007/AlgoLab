from unittest.mock import patch

import pytest

from sortlab import cli
from sortlab.core import ALGORITHM_REGISTRY, ALGORITHM_SPECS, get_algorithm_spec


def test_registry_has_all_ten_algorithms():
    assert len(ALGORITHM_SPECS) == 10
    assert list(ALGORITHM_REGISTRY.keys()) == [str(i) for i in range(1, 11)]
    assert get_algorithm_spec("quick_sort").choice == "5"
    assert get_algorithm_spec("Counting Sort").integer_only is True
    assert get_algorithm_spec("Radix Sort").integer_only is True
    with pytest.raises(ValueError):
        get_algorithm_spec("unknown")


def test_parse_values_valid_and_invalid():
    assert cli.parse_values("3, 1 2") == [3, 1, 2]
    assert cli.parse_values("3.0, -2.5 0") == [3, -2.5, 0]
    large = 10**25
    assert cli.parse_values(f"{large} 1") == [large, 1]

    for bad in ("", "   ", "1, abc", "nan", "inf", "-inf"):
        with pytest.raises(ValueError):
            cli.parse_values(bad)


@pytest.mark.parametrize("choice", [str(i) for i in range(1, 11)])
def test_run_algorithm_dispatches_all_ten(choice):
    values = [5, -2, 3, 0, 5, 1]
    assert cli.run_algorithm(choice, values) == sorted(values)


@pytest.mark.parametrize("choice", ["8", "9"])
def test_run_algorithm_rejects_floats_for_integer_only_sorts(choice):
    with pytest.raises(ValueError, match="integers only"):
        cli.run_algorithm(choice, [1, 2.5, 3])


@pytest.mark.parametrize("choice", [str(i) for i in range(1, 11)])
def test_cli_automatically_launches_visualization_and_returns_to_menu(
    choice, capsys
):
    inputs = iter([choice, "4, 1, -2, 3", "0"])
    with (
        patch("builtins.input", side_effect=lambda _prompt="": next(inputs)),
        patch("sortlab.cli.visualize_algorithm") as mock_vis,
    ):
        exit_code = cli.main([])

    assert exit_code == 0
    mock_vis.assert_called_once()
    called_spec, called_values = mock_vis.call_args.args
    assert called_spec.choice == choice
    assert called_values == [4, 1, -2, 3]
    out = capsys.readouterr().out
    assert "Sorted:    [-2, 1, 3, 4]" in out
    assert "Goodbye!" in out


def test_cli_rejects_floats_for_counting_and_radix_before_visualizing(capsys):
    inputs = iter(["8", "1 2.5 3", "9", "4 1.2", "0"])
    with (
        patch("builtins.input", side_effect=lambda _prompt="": next(inputs)),
        patch("sortlab.cli.visualize_algorithm") as mock_vis,
    ):
        exit_code = cli.main([])

    assert exit_code == 0
    mock_vis.assert_not_called()
    out = capsys.readouterr().out
    assert "Counting Sort accepts integers only" in out
    assert "Radix Sort accepts integers only" in out


def test_cli_handles_invalid_menu_choice_and_missing_matplotlib(capsys):
    inputs = iter(["99", "1", "3 1 2", "0"])
    with (
        patch("builtins.input", side_effect=lambda _prompt="": next(inputs)),
        patch(
            "sortlab.cli.visualize_algorithm",
            side_effect=ImportError("Matplotlib is optional"),
        ),
    ):
        exit_code = cli.main([])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Invalid choice" in out
    assert "Visualization unavailable" in out
    assert "Goodbye!" in out


def test_cli_list_and_no_vis_flags(capsys):
    assert cli.main(["--list"]) == 0
    listed = capsys.readouterr().out
    assert "1. Bubble Sort" in listed
    assert "10. Bucket Sort" in listed

    inputs = iter(["4", "3 1 2", "0"])
    with (
        patch("builtins.input", side_effect=lambda _prompt="": next(inputs)),
        patch("sortlab.cli.visualize_algorithm") as mock_vis,
    ):
        assert cli.main(["--no-vis"]) == 0
    mock_vis.assert_not_called()
