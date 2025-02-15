# sourcery skip: no-relative-imports
from automata.eval import CodeWritingAction, OpenAIFunctionCallAction
from automata.tasks.task_base import TaskStatus

from .conftest import (
    EXPECTED_CODE_ACTIONS,
    EXPECTED_FUNCTION_ACTIONS,
    mock_openai_response_with_function_completion_message_final,
    params,
)

# TODO - Refactor test eval into multiple tests
# TODO - Include more tests for CodeWriting / FunctionCalling
# which include more exotic types


def test_generate_function_eval_result_match(
    conversation_db,
    tasks,
    function_evaluator,
    setup,
):
    task = tasks[0]
    mock_openai_chatcompletion_create, automata_agent, task_executor = setup
    mock_openai_chatcompletion_create.side_effect = params[
        "test_generate_function_eval_result_match_responses"
    ]
    # Act
    result = function_evaluator.generate_eval_result(
        task, EXPECTED_FUNCTION_ACTIONS, task_executor, run_id="test"
    )

    # Assert
    assert result.is_full_match
    assert result.match_results == {
        action: True for action in EXPECTED_FUNCTION_ACTIONS
    }
    assert result.extra_actions == [
        OpenAIFunctionCallAction(
            name="call_termination", arguments={"result": "Success"}
        )
    ]

    assert task.status == TaskStatus.SUCCESS
    assert task.result == "Success"

    saved_messages = conversation_db.get_messages(automata_agent.session_id)
    assert len(saved_messages) == 11


def test_generate_eval_result_no_match(
    conversation_db, tasks, function_evaluator, setup
):
    task = tasks[0]
    mock_openai_chatcompletion_create, automata_agent, task_executor = setup
    mock_openai_chatcompletion_create.side_effect = params[
        "test_generate_eval_result_no_match_responses"
    ]

    # Act
    result = function_evaluator.generate_eval_result(
        task, EXPECTED_FUNCTION_ACTIONS, task_executor, run_id="test"
    )

    # Assert
    assert not result.is_full_match
    assert result.match_results == {
        action: False for action in EXPECTED_FUNCTION_ACTIONS
    }
    assert result.extra_actions == [
        OpenAIFunctionCallAction(
            name="function3", arguments={"arg3": "value3"}
        ),
        OpenAIFunctionCallAction(
            name="call_termination", arguments={"result": "Success"}
        ),
    ]


def test_generate_eval_result_partial_match(
    conversation_db, tasks, function_evaluator, setup
):
    task = tasks[0]
    mock_openai_chatcompletion_create, automata_agent, task_executor = setup
    mock_openai_chatcompletion_create.side_effect = params[
        "test_generate_eval_result_partial_match"
    ]

    # Act
    result = function_evaluator.generate_eval_result(
        task, EXPECTED_FUNCTION_ACTIONS, task_executor, run_id="test"
    )

    # Assert
    assert not result.is_full_match
    assert result.match_results == {
        EXPECTED_FUNCTION_ACTIONS[0]: True,
        EXPECTED_FUNCTION_ACTIONS[1]: False,
    }
    assert result.extra_actions == [
        OpenAIFunctionCallAction(
            name="call_termination", arguments={"result": "Success"}
        ),
    ]


def test_generate_code_writing_eval_result_match(
    conversation_db, tasks, code_evaluator, setup
):
    task = tasks[0]
    mock_openai_chatcompletion_create, automata_agent, task_executor = setup
    mock_openai_chatcompletion_create.side_effect = params[
        "test_generate_code_writing_eval_result_match"
    ]

    # Act
    result = code_evaluator.generate_eval_result(
        task, EXPECTED_CODE_ACTIONS, task_executor, run_id="test"
    )

    # Assert
    assert result.is_full_match
    assert result.match_results == {
        action: True for action in EXPECTED_CODE_ACTIONS
    }
    assert result.extra_actions == [
        CodeWritingAction(object_value_repr="3.14", object_type="float")
    ]


def test_generate_code_writing_eval_result_no_match(
    conversation_db, tasks, code_evaluator, setup
):
    task = tasks[0]
    mock_openai_chatcompletion_create, automata_agent, task_executor = setup
    mock_openai_chatcompletion_create.side_effect = params[
        "test_generate_code_writing_eval_result_no_match"
    ]

    # Act
    result = code_evaluator.generate_eval_result(
        task, EXPECTED_CODE_ACTIONS, task_executor, run_id="test"
    )

    # Assert
    assert not result.is_full_match
    assert result.match_results == {
        action: False for action in EXPECTED_CODE_ACTIONS
    }
    assert result.extra_actions == []


def test_generate_code_writing_eval_result_partial_match(
    conversation_db, tasks, code_evaluator, setup
):
    task = tasks[0]
    mock_openai_chatcompletion_create, automata_agent, task_executor = setup
    mock_openai_chatcompletion_create.side_effect = [
        {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "```python\nx = 1```",
                    }
                }
            ]
        },
        mock_openai_response_with_function_completion_message_final(),
    ]

    # Act
    result = code_evaluator.generate_eval_result(
        task,
        EXPECTED_CODE_ACTIONS,
        task_executor,
        session_id=None,
        run_id="test",
    )

    # Assert
    assert not result.is_full_match
    assert result.match_results == {
        EXPECTED_CODE_ACTIONS[0]: True,
        EXPECTED_CODE_ACTIONS[1]: False,
    }
    assert result.extra_actions == []


def test_composite_eval_result_match(
    conversation_db, tasks, composite_evaluator, setup
):
    task = tasks[0]
    mock_openai_chatcompletion_create, automata_agent, task_executor = setup
    mock_openai_chatcompletion_create.side_effect = params[
        "test_composite_eval_result_match"
    ]

    expected_actions = [
        EXPECTED_FUNCTION_ACTIONS[0],
        EXPECTED_CODE_ACTIONS[0],
        OpenAIFunctionCallAction(
            name="call_termination", arguments={"result": "Success"}
        ),
    ]

    result = composite_evaluator.generate_eval_result(
        task, expected_actions, task_executor, session_id=None, run_id="test"
    )

    assert result.is_full_match
    assert result.match_results == {
        action: True for action in expected_actions
    }
    assert result.extra_actions == [
        CodeWritingAction(object_value_repr="3.14", object_type="float"),
    ]


def test_composite_eval_no_match(
    conversation_db, tasks, composite_evaluator, setup
):
    task = tasks[0]

    mock_openai_chatcompletion_create, automata_agent, task_executor = setup
    mock_openai_chatcompletion_create.side_effect = params[
        "test_composite_eval_no_match"
    ]

    expected_actions = [
        EXPECTED_FUNCTION_ACTIONS[0],
        EXPECTED_CODE_ACTIONS[0],
    ]

    result = composite_evaluator.generate_eval_result(
        task, expected_actions, task_executor, session_id=None, run_id="test"
    )

    assert result.is_full_match is False
    assert result.match_results == {
        EXPECTED_FUNCTION_ACTIONS[0]: False,
        EXPECTED_CODE_ACTIONS[0]: False,
    }
    assert result.extra_actions == [
        OpenAIFunctionCallAction(
            name="call_termination", arguments={"result": "Success"}
        )
    ]


def test_code_execution_error(composite_evaluator, tasks, setup):
    task = tasks[0]

    mock_openai_chatcompletion_create, automata_agent, task_executor = setup
    mock_openai_chatcompletion_create.side_effect = params[
        "test_composite_eval_no_match"
    ]

    expected_actions = [
        EXPECTED_FUNCTION_ACTIONS[0],
        EXPECTED_CODE_ACTIONS[0],
    ]

    result = composite_evaluator.generate_eval_result(
        task, expected_actions, task_executor, session_id=None, run_id="test"
    )

    assert result.is_full_match is False
    assert result.match_results == {
        EXPECTED_FUNCTION_ACTIONS[0]: False,
        EXPECTED_CODE_ACTIONS[0]: False,
    }
    assert result.extra_actions == [
        OpenAIFunctionCallAction(
            name="call_termination", arguments={"result": "Success"}
        )
    ]


def test_partial_matches():
    obj1 = CodeWritingAction(
        object_type="int", object_value_repr="1", error=None
    )
    obj2 = CodeWritingAction(
        object_type="float", object_value_repr="2.0", error=None
    )

    action_1 = CodeWritingAction(
        object_type=str(type(obj1)), object_value_repr=repr(obj1), error=None
    )

    action_2 = CodeWritingAction(
        object_type=str(type(obj2)), object_value_repr=repr(obj2), error=None
    )

    assert action_1 == action_2
