""" test feed download """

from act.scio.feeds import extract


def test_safe_download() -> None:
    """test for safe download"""
    assert extract.replace_unsafe_filename_characters("test%.[x y z]") == "test.x_y_z"


def test_santize_filename() -> None:
    """Test for filename lengtt and sane name"""

    wrong = "/home/scio/.cache/scio-feeds/download/June_2_6122015_Consulting_Thought_Leadership_quotProactively_Engagedâ_Questions_Executives_Should_Ask_Their_Security_Teams_quotquot-Many_breaches_occur_as_a_result_of_executive_decisions_made_woutfull_knowledge_of_the_peopleprocesses_needed_to_prevent_them__-Offersspecific_questions_that_execs_should_ask_to_understand_and_prevent_abreachquot_Jim_Aldridge_Kyrk_Content_Finalized_Global________June_26122015_Consulting_Thought_Leadership_quotProactively_Engaged_âQuestions_Executives_Should_Ask_Their_Security_Teams_quot_quot-Manybreaches_occur_as_a_result_of_executive_decisions_made_wout_fullknowledge_of_the_peopleprocesses_needed_to_prevent_them__-Offersspecific_questions_that_execs_should_ask_to_understand_and_prevent_abreachquot_Jim_Aldridge_Kyrk_Content_Finalized_GlobCaching_Out_TheValue_of_Shimcache_for_Investigators.html"  # noqa E501
    correct = "/home/scio/.cache/scio-feeds/download/June_2_6122015_Consulting_Thought_Leadership_quotProactively_Engagedâ_Questions_Executives_Should_Ask_Their_Security_Teams_quotquot-Many_breaches_occur_as_a_result_of_executive_decisions_made_woutfull_knowledge_of_the_peopleprocesses_needed_to_preve.html"  # noqa: E501

    assert extract.sanitize_filename(wrong) == correct


def test_safe_filename() -> None:
    """Test that / are correctly removed"""

    filename = "Example / This is a %title%"

    path = extract.create_storage_path(filename, "html", "/", "/tmp/", "download")

    assert path == "/tmp/download/Example__This_is_a_title.html"
