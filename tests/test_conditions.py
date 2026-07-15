import pytest

from muara.engine.state import GameState
from muara.models.chapter import ConditionOperator, FlagCondition
from muara.models.save_state import SaveState


@pytest.mark.parametrize(
    "operator,flag_value,condition_value,expected",
    [
        (ConditionOperator.EQ, 3, 3, True),
        (ConditionOperator.EQ, 3, 4, False),
        (ConditionOperator.NEQ, 3, 4, True),
        (ConditionOperator.NEQ, 3, 3, False),
        (ConditionOperator.GT, 5, 3, True),
        (ConditionOperator.GT, 2, 3, False),
        (ConditionOperator.GTE, 3, 3, True),
        (ConditionOperator.GTE, 2, 3, False),
        (ConditionOperator.LT, 2, 3, True),
        (ConditionOperator.LT, 3, 3, False),
        (ConditionOperator.LTE, 3, 3, True),
        (ConditionOperator.LTE, 4, 3, False),
    ],
)
def test_evaluate_all_operators(operator, flag_value, condition_value, expected):
    condition = FlagCondition(flag="trust_jaya", operator=operator, value=condition_value)
    assert condition.evaluate({"trust_jaya": flag_value}) is expected


def test_evaluate_missing_flag_bool_default_false():
    condition = FlagCondition(flag="sudah_lapor", operator=ConditionOperator.EQ, value=True)
    assert condition.evaluate({}) is False


def test_evaluate_missing_flag_int_default_zero():
    condition = FlagCondition(flag="trust_jaya", operator=ConditionOperator.EQ, value=0)
    assert condition.evaluate({}) is True


def test_evaluate_missing_flag_str_default_empty():
    condition = FlagCondition(flag="nama_saksi", operator=ConditionOperator.EQ, value="")
    assert condition.evaluate({}) is True


def test_evaluate_relational_operator_type_mismatch_raises_type_error():
    condition = FlagCondition(flag="trust_jaya", operator=ConditionOperator.GTE, value=3)
    with pytest.raises(TypeError):
        condition.evaluate({"trust_jaya": "bukan angka"})


# --- GameState.evaluate_condition() edge case tests ---

def _make_state(flags):
    return GameState(SaveState(
        save_id="test",
        current_chapter="test",
        current_scene="test",
        flags=flags,
    ))


def test_empty_condition():
    state = _make_state({})
    assert state.evaluate_condition("") is False


def test_truthy_check_unset_flag():
    state = _make_state({})
    assert state.evaluate_condition("nonexistent_flag") is False


def test_truthy_check_existing_flag():
    state = _make_state({"melapor": True})
    assert state.evaluate_condition("melapor") is True


def test_equality_unset_flag():
    state = _make_state({})
    assert state.evaluate_condition("nonexistent_flag == true") is False


def test_numeric_unset_flag():
    state = _make_state({})
    assert state.evaluate_condition("nonexistent_flag >= 5") is False


def test_negation_unset_flag():
    state = _make_state({})
    assert state.evaluate_condition("not nonexistent_flag") is True


def test_negation_truthy_flag():
    state = _make_state({"melapor": True})
    assert state.evaluate_condition("not melapor") is False


def test_ambiguous_operator():
    state = _make_state({"flag": 5})
    assert state.evaluate_condition("flag >= == 5") is False


def test_ge_numeric():
    state = _make_state({"skor": 10})
    assert state.evaluate_condition("skor >= 5") is True
    assert state.evaluate_condition("skor >= 15") is False


def test_le_numeric():
    state = _make_state({"skor": 3})
    assert state.evaluate_condition("skor <= 5") is True
    assert state.evaluate_condition("skor <= 1") is False


def test_ge_non_numeric_val():
    state = _make_state({"skor": 10})
    assert state.evaluate_condition("skor >= abc") is False


def test_le_non_numeric_val():
    state = _make_state({"skor": 3})
    assert state.evaluate_condition("skor <= xyz") is False


def test_bool_eq_true():
    state = _make_state({"melapor": True})
    assert state.evaluate_condition("melapor == true") is True
    state = _make_state({"melapor": False})
    assert state.evaluate_condition("melapor == true") is False


def test_bool_eq_false():
    state = _make_state({"melapor": False})
    assert state.evaluate_condition("melapor == false") is True
    state = _make_state({"melapor": True})
    assert state.evaluate_condition("melapor == false") is False


def test_bool_ne_true():
    state = _make_state({"melapor": False})
    assert state.evaluate_condition("melapor != true") is True
    state = _make_state({"melapor": True})
    assert state.evaluate_condition("melapor != true") is False


def test_bool_ne_false():
    state = _make_state({"melapor": True})
    assert state.evaluate_condition("melapor != false") is True
    state = _make_state({"melapor": False})
    assert state.evaluate_condition("melapor != false") is False


def test_str_eq_true():
    state = _make_state({"status": "true"})
    assert state.evaluate_condition("status == true") is False


def test_str_eq_false():
    state = _make_state({"status": "false"})
    assert state.evaluate_condition("status == false") is False


def test_str_eq_int():
    state = _make_state({"chapter": 4})
    assert state.evaluate_condition("chapter == 4") is True
    assert state.evaluate_condition("chapter == 5") is False


def test_str_eq_string_val():
    state = _make_state({"chapter_5_choice": "simpan"})
    assert state.evaluate_condition("chapter_5_choice == simpan") is True
    assert state.evaluate_condition("chapter_5_choice == hancurkan") is False


def test_ne_int():
    state = _make_state({"chapter": 4})
    assert state.evaluate_condition("chapter != 5") is True
    assert state.evaluate_condition("chapter != 4") is False


def test_ne_true_str():
    state = _make_state({"status": "true"})
    assert state.evaluate_condition("status != true") is True


def test_ne_false_str():
    state = _make_state({"status": "false"})
    assert state.evaluate_condition("status != false") is True


def test_ne_string_val():
    state = _make_state({"chapter_5_choice": "simpan"})
    assert state.evaluate_condition("chapter_5_choice != hancurkan") is True
    assert state.evaluate_condition("chapter_5_choice != simpan") is False


def test_unsupported_op_fallback():
    state = _make_state({"flag": 5})
    assert state.evaluate_condition("flag > 3") is False
