# Tests — How They Work

## What are tests?

Tests are small programs that check your app works correctly.
Instead of manually testing every feature after every code change,
tests do it automatically in seconds.

## How to run tests

From the project root:

```bash
# Run all tests with colorful verbose output
./run_tests.sh

# Or run directly with pytest
cd backend
python -m pytest tests/ -v --tb=short
```

## What each file tests

| File | What it tests |
|------|--------------|
| `test_selector.py` | Does the style selector pick the right style for each photo type? |
| `test_parser.py` | Does the parser correctly handle Gemini's JSON responses (including bad ones)? |
| `conftest.py` | Shared test data (fake metadata for different photo scenarios) |

## How to read test output

When you run tests, you'll see output like:

```
test_selector.py::test_golden_hour_outdoor_gets_warm_golden PASSED
test_selector.py::test_flat_daylight_gets_bright_airy PASSED
test_selector.py::test_bad_color_gets_black_white PASSED
test_parser.py::test_valid_json_parses_correctly PASSED
test_parser.py::test_invalid_json_returns_none PASSED
```

- **PASSED** = the test worked correctly (green)
- **FAILED** = something is broken (red) — read the error message to see what
- **ERROR** = the test itself crashed (usually a bug in the test)

## How to write a new test

Tests are just Python functions that start with `test_`:

```python
def test_my_feature():
    # 1. Set up the input
    metadata = {"scene_type": "outdoor", "lighting": "golden_hour", ...}

    # 2. Run the code
    result = select_styles_from_dict(metadata)

    # 3. Check the output
    assert result["primary_style"] == "warm_golden"
```

The `assert` line is the key — it says "this MUST be true, or the test fails."
