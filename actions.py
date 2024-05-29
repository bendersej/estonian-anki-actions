import requests
from typing import Annotated, List
from sema4ai.actions import action, Secret
from robocorp import browser
from pydantic import BaseModel, Field
from urllib.parse import quote_plus


@action(is_consequential=False)
def add_card_to_current_deck(
    user_email: Secret, user_password: Secret, front_value: str, back_value: str
) -> str:
    """Adds a card to the current Anki deck.

    Args:
        user_email: The email used to log into Anki Web
        user_password: The password used to log into Anki Web
        front_value: Text to save into the front card of the Anki Deck
        back_value: Text to save into the back card of the Anki Deck

    Returns:
        Message indicating that the card was successfully saved.
    """
    browser.configure(browser_engine="chromium", headless=True)

    page = browser.goto("https://ankiweb.net/account/login")
    page.fill("input[placeholder='Email']", user_email.value)
    page.fill("input[placeholder='Password']", user_password.value)
    page.click("text='Log In'")
    page.click("text='Add'")

    page.fill('div:has(span:text("Front")) > div > div', front_value)
    page.fill('div:has(span:text("Back")) > div > div', back_value)

    page.click("button:text('Add')")

    page.close()

    return "The card was successfully saved"


@action(is_consequential=False)
def is_card_in_current_deck(
    user_email: Secret, user_password: Secret, search: str
) -> str:
    browser.configure(browser_engine="chromium", headless=True)

    page = browser.goto("https://ankiweb.net/account/login")
    page.fill("input[placeholder='Email']", user_email.value)
    page.fill("input[placeholder='Password']", user_password.value)
    page.click("text='Log In'")
    page.click("text='Search'")

    page.fill("input[placeholder='Search']", f"deck:current {search}")
    page.click("button:text('Search')")

    try:
        page.wait_for_selector("table > tr > td", timeout=500)
        return "The card is already in the deck"
    except Exception:
        return "The card is not in the deck"


class OutputData(BaseModel):
    estonian_word: Annotated[str, Field(description="The estonian word.")]
    english_word: Annotated[str, Field(description="The english word.")]
    word_forms: Annotated[
        List[str],
        Field(description="The 3 main forms of the word: nimetav, omastav, osastav."),
    ]


@action(is_consequential=False)
def get_word(word: str, is_english_word: bool) -> OutputData:
    """Looks up a word, either in estonian or in english.

    Args:
        word: The word to look up
        is_english_word: Whether the word is an english word or not

    Returns:
        The estonian word, the english word as well as the three word forms for this estonian word.
    """

    base_url = f"https://api.sonapi.ee/v2/{quote_plus(word)}"
    params = {"lg": "en"} if is_english_word else {}

    response = requests.get(base_url, params=params)
    data = response.json()

    word_forms_list = data.get("searchResult", [])[0].get("wordForms", [])[:3]
    word_forms = [wf["value"] for wf in word_forms_list]

    translations = data.get("translations", [])[0].get("translations", [])
    english_translation = translations[0]

    english_word = word if is_english_word else english_translation
    estonian_word = data.get("estonianWord", "")

    return OutputData(
        estonian_word=estonian_word, english_word=english_word, word_forms=word_forms
    )
