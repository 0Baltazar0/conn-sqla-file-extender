def must_valid_input(
    question: str, responses: list[str] = ["Y", "n"], case_insensitive: bool = True
) -> str:
    resp = input(f"{question}? [{'/'.join(responses)}]").lower()
    sanitized_responses = [r if not case_insensitive else r.lower() for r in responses]
    while resp not in sanitized_responses:
        resp = input(
            f"Answer not accepted, {question}? [{'/'.join(responses)}]",
        )
        resp = resp if case_insensitive else resp.lower()
    return resp


def must_valid_from_list(
    main_question: str, templated_row: str, values: list[str], abort_able: bool = True
) -> str:
    answer = must_valid_input(
        "\n".join(
            [main_question] + ["Press x to abort"]
            if abort_able
            else []
            + [
                templated_row % v + f" >> [{i}]"
                for v, i in zip(values, range(len(values)))
            ]
        ),
        [str(i) for i in range(len(values))] + ["x"] if abort_able else [],
    )
    if answer != "x":
        return values[int(answer)]

    return answer
