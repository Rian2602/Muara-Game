import pytest

from muara.models.chapter import ConditionOperator, FlagCondition


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
