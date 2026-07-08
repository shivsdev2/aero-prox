"""
Unit tests for main.py.

Tests cover:
- prompt_airport: valid ICAO, invalid ICAO retry, case-insensitivity
- prompt_radius: valid positive integer, invalid input retry
- parse_args: CLI argument parsing
- main(): end-to-end flow with mocked dependencies, including CLI args
- KeyboardInterrupt handling
- Unexpected exception handling
"""

from unittest.mock import patch

import pytest

from main import parse_args, prompt_airport, prompt_radius


class TestParseArgs:
    """Tests for the parse_args function."""

    def test_no_args_returns_defaults(self):
        """No arguments should result in None defaults."""
        args = parse_args([])
        assert args.icao is None
        assert args.radius is None
        assert args.lat is None
        assert args.lon is None

    def test_icao_only(self):
        """Only --icao provided."""
        args = parse_args(["--icao", "VERC"])
        assert args.icao == "VERC"
        assert args.radius is None
        assert args.lat is None
        assert args.lon is None

    def test_radius_only(self):
        """Only --radius provided."""
        args = parse_args(["--radius", "5000"])
        assert args.icao is None
        assert args.radius == 5000

    def test_both_args(self):
        """Both --icao and --radius provided."""
        args = parse_args(["--icao", "KJFK", "--radius", "10000"])
        assert args.icao == "KJFK"
        assert args.radius == 10000

    def test_radius_string_rejected(self):
        """argparse should reject non-integer radius."""
        with pytest.raises(SystemExit):
            parse_args(["--radius", "abc"])

    def test_lat_lon_args(self):
        """--lat and --lon should parse as floats."""
        args = parse_args(["--lat", "23.34", "--lon", "85.31"])
        assert args.lat == 23.34
        assert args.lon == 85.31


class TestPromptAirport:
    """Tests for the prompt_airport function."""

    def test_valid_icao_returns_airport(self, mock_airportsdata):
        """A valid ICAO code should return the corresponding airport dict."""
        airports = mock_airportsdata.return_value
        with patch("builtins.input", return_value="VERC"):
            result = prompt_airport(airports)
        assert result == {
            "name": "Birsa Munda Airport",
            "city": "Ranchi",
            "country": "India",
            "iata": "IXR",
            "lat": 23.3147,
            "lon": 85.3217,
        }

    def test_case_insensitive_icao(self, mock_airportsdata):
        """ICAO codes should be matched case-insensitively (uppercased internally)."""
        airports = mock_airportsdata.return_value
        with patch("builtins.input", return_value="verc"):
            result = prompt_airport(airports)
        assert result["name"] == "Birsa Munda Airport"

    def test_invalid_then_valid_icao(self, mock_airportsdata):
        """An invalid ICAO should prompt again, then a valid one should succeed."""
        airports = mock_airportsdata.return_value
        inputs = iter(["XXXX", "VERC"])
        with patch("builtins.input", side_effect=inputs):
            result = prompt_airport(airports)
        assert result["name"] == "Birsa Munda Airport"

    def test_invalid_icao_shows_error_message(self, mock_airportsdata, capsys):
        """An invalid ICAO should print an error message before retrying."""
        airports = mock_airportsdata.return_value
        inputs = iter(["ZZZZ", "VERC"])
        with patch("builtins.input", side_effect=inputs):
            prompt_airport(airports)
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower()


class TestPromptRadius:
    """Tests for the prompt_radius function."""

    def test_valid_positive_integer(self):
        """A valid positive integer should be returned as an int."""
        with patch("builtins.input", return_value="5000"):
            result = prompt_radius()
        assert result == 5000

    def test_zero_rejected(self):
        """Zero should be rejected (must be positive)."""
        inputs = iter(["0", "1000"])
        with patch("builtins.input", side_effect=inputs):
            result = prompt_radius()
        assert result == 1000

    def test_negative_rejected(self):
        """Negative numbers should be rejected."""
        inputs = iter(["-5", "1000"])
        with patch("builtins.input", side_effect=inputs):
            result = prompt_radius()
        assert result == 1000

    def test_non_numeric_rejected(self):
        """Non-numeric input should be rejected."""
        inputs = iter(["abc", "1000"])
        with patch("builtins.input", side_effect=inputs):
            result = prompt_radius()
        assert result == 1000

    def test_float_rejected(self):
        """Floating-point input should be rejected (int() will raise ValueError)."""
        inputs = iter(["3.14", "1000"])
        with patch("builtins.input", side_effect=inputs):
            result = prompt_radius()
        assert result == 1000


class TestMainFunction:
    """Tests for the main() entry point."""

    def test_main_successful_run(self, mock_airportsdata, mock_fr_api):
        """
        A full run of main() with mocked dependencies should complete
        without error and call run_tracking.
        """
        with (
            patch("main.airportsdata.load", mock_airportsdata),
            patch("builtins.input", side_effect=["VERC", "5000", "23.34", "85.31"]),
            patch("main.run_tracking") as mock_run_tracking,
            patch("main.sys.argv", ["prog"]),
        ):
            from main import main

            main()

        mock_run_tracking.assert_called_once()
        call_kwargs = mock_run_tracking.call_args.kwargs
        args, _ = mock_run_tracking.call_args
        lat, lon, name, radius = args
        assert lat == 23.3147
        assert lon == 85.3217
        assert name == "Birsa Munda Airport"
        assert radius == 5000
        assert call_kwargs.get("user_lat") == 23.34
        assert call_kwargs.get("user_lon") == 85.31

    def test_keyboard_interrupt_handled(self, mock_airportsdata, capsys):
        """A KeyboardInterrupt during tracking should print 'Stopped by user.'"""
        with (
            patch("main.airportsdata.load", mock_airportsdata),
            patch("builtins.input", side_effect=["VERC", "5000", "23.34", "85.31"]),
            patch("main.run_tracking", side_effect=KeyboardInterrupt),
            patch("main.sys.argv", ["prog"]),
        ):
            from main import main

            main()

        captured = capsys.readouterr()
        assert "Stopped by user" in captured.out

    def test_unexpected_exception_handled(self, mock_airportsdata):
        """An unexpected exception should print the error and exit."""
        with (
            patch("main.airportsdata.load", mock_airportsdata),
            patch("builtins.input", side_effect=["VERC", "5000", "23.34", "85.31"]),
            patch("main.run_tracking", side_effect=RuntimeError("boom")),
            patch("main.sys.argv", ["prog"]),
            pytest.raises(SystemExit) as exc_info,
        ):
            from main import main

            main()

        assert exc_info.value.code == 1

    # ------------------------------------------------------------------
    # Tests for CLI argument usage
    # ------------------------------------------------------------------

    def test_main_with_cli_args(self, mock_airportsdata, mock_fr_api):
        """
        main() should accept --icao, --radius, --lat, --lon via sys.argv
        and skip all interactive prompts.
        """
        test_argv = [
            "prog",
            "--icao",
            "VERC",
            "--radius",
            "8000",
            "--lat",
            "23.34",
            "--lon",
            "85.31",
        ]
        with (
            patch("main.airportsdata.load", mock_airportsdata),
            patch("main.run_tracking") as mock_run_tracking,
            patch("main.sys.argv", test_argv),
        ):
            from main import main

            main()

        mock_run_tracking.assert_called_once()
        args, _ = mock_run_tracking.call_args
        lat, lon, name, radius = args
        call_kwargs = mock_run_tracking.call_args.kwargs
        assert lat == 23.3147
        assert lon == 85.3217
        assert name == "Birsa Munda Airport"
        assert radius == 8000
        assert call_kwargs.get("user_lat") == 23.34
        assert call_kwargs.get("user_lon") == 85.31

    def test_main_with_invalid_icao_cli_exits(self, mock_airportsdata):
        """main() should exit with error if --icao is not found."""
        test_argv = ["prog", "--icao", "ZZZZ", "--radius", "5000"]
        with (
            patch("main.airportsdata.load", mock_airportsdata),
            patch("main.sys.argv", test_argv),
            pytest.raises(SystemExit) as exc_info,
        ):
            from main import main

            main()

        assert exc_info.value.code == 1

    def test_main_with_invalid_radius_cli_exits(self, mock_airportsdata):
        """main() should exit with error if --radius is zero or negative."""
        test_argv = ["prog", "--icao", "VERC", "--radius", "0"]
        with (
            patch("main.airportsdata.load", mock_airportsdata),
            patch("main.sys.argv", test_argv),
            pytest.raises(SystemExit) as exc_info,
        ):
            from main import main

            main()

        assert exc_info.value.code == 1

    def test_main_with_cli_icao_only_interactive_radius(
        self, mock_airportsdata, mock_fr_api
    ):
        """--icao supplied, but --radius should fall back to interactive prompt."""
        test_argv = ["prog", "--icao", "VERC"]
        with (
            patch("main.airportsdata.load", mock_airportsdata),
            patch("builtins.input", side_effect=["12000", "23.34", "85.31"]),
            patch("main.run_tracking") as mock_run_tracking,
            patch("main.sys.argv", test_argv),
        ):
            from main import main

            main()

        mock_run_tracking.assert_called_once()
        args, _ = mock_run_tracking.call_args
        assert args[3] == 12000
