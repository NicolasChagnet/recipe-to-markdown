import os
import re
import shutil
import textwrap
from pathlib import Path

import click
import inquirer
import requests
from deep_translator import GoogleTranslator
from loguru import logger
from recipe_scrapers import AbstractScraper, scrape_html
from rich.console import Console
from rich.markdown import Markdown

DIRECTORY = Path("./local/")
REGEX_SPLIT = r"(\d+)(?!.*\d)"  # Used to split a string after its last number

console = Console()

click_category = click.option("--category", type=str, default="", help="Category in which the recipe belongs.")
click_extras = click.option(
    "--extra",
    "-e",
    "extras",
    type=click.Choice(["veggie", "spicy", "sweet", "salty", "sour", "bitter", "umami"], case_sensitive=False),
    multiple=True,
    default=[],
    help="Extra tags for the recipe (among veggie, spicy, sweet, salty, sour, bitter, and umami).",
)
click_translate = click.option(
    "--translate", is_flag=True, default=False, help="Translate the content of the recipe using Google Translate."
)
click_name = click.option("--name", "-n", type=str, default=None, help="Name of the recipe.")


@click.group()
def cli() -> None:
    pass


def camel_case_splitter(word: str) -> str:
    """Convert a camelCase word into a sentence.

    Args:
        word (str): CamelCase word

    Returns:
        str: Sentence created from CamelCase word
    """
    split = re.sub("([A-Z][a-z]+)", r" \1", re.sub("([A-Z]+)", r" \1", word)).split()
    return " ".join(split).capitalize()


def get_console_width() -> int:
    """Get the current width of the console, with a maximum limit."""
    return min(shutil.get_terminal_size().columns, 80)


def clear_console() -> None:
    """Clear the console."""
    if os.name == "nt":  # For Windows
        os.system("cls")
    else:  # For Unix-based systems (Linux, macOS)
        os.system("clear")


def format_title(scraper: dict) -> str:
    """Format recipe title."""
    return scraper.title().replace(" ", "-")


def scrape_recipe(recipe_url: str) -> type[AbstractScraper]:
    """Scrape the recipe webpage using the recipe_scraper module.

    Args:
        recipe_url (str): URL of the recipe.

    Returns:
        AbstractScraper: instance of a subclass of AbstractScraper containing the recipe information.
    """
    try:
        html = requests.get(recipe_url, headers={"User-Agent": "recipe2md"}).content
        scraper = scrape_html(html, org_url=recipe_url, wild_mode=True)
        return scraper
    except Exception as e:
        logger.error(f"Could not scrape recipe, error: {str(e)}")
        return None


def generate_markdown(
    recipe_url: str, name: str, category: str, extras: list[str], translate: bool
) -> (str, str, type[AbstractScraper]):
    """Given a recipe URL, scrape and generate the markdown content.

    Args:
        recipe_url (str): url string from a recipe website.
        name (str): Name of recipe for the metadata and filename.
        category (str): Category in which the recipe belongs.
        extras (list[str]): Extra tags for the recipe (among spicy, sweet, salty, sour, bitter, and umami).
        translate (bool): Flag on whether to translate the recipe using Google Translate.

    Returns:
        (str, str, AbstractScraper): Markdown content for the recipe, image filename and scraped data dictionary.
    """
    scraper = scrape_recipe(recipe_url)
    if scraper is None:
        return "", "", AbstractScraper()

    # Format title
    title = scraper.title() if name is None else name
    ingredients = scraper.ingredients()
    instructions = scraper.instructions_list()

    # Download accompanying image
    image_file_extension = scraper.image().split(".")[-1]
    image_filename = f"{format_title(title)}.{image_file_extension}"

    # Handle translation if flagged
    if translate:
        translator = GoogleTranslator(source="auto", target="en")
        title = translator.translate(title)
        ingredients = map(translator.translate, ingredients)
        instructions = map(translator.translate, instructions)

    # Markdown content
    markdown_content = ""
    markdown_content += textwrap.dedent(f"""\
            ---
            title: {title.capitalize()}
            category: {category.capitalize()}
            source: {recipe_url}
            image: {image_filename}
            size: {scraper.yields()}
            time: {scraper.total_time()} mins\n""")
    # Nutrition components
    if len(scraper.nutrients()) > 0:
        markdown_content += "nutrition:\n"
        for nutrient, quantity in scraper.nutrients().items():
            markdown_content += f"\t- {camel_case_splitter(nutrient).replace(' content', '')} {quantity}\n"
    for extra in extras:
        markdown_content += f"{extra}: x\n"
    markdown_content += "---\n\n"
    # Print all ingredients
    for ingredient in ingredients:
        markdown_content += f"* {ingredient}\n"
    markdown_content += "\n"
    # Print all instructions
    markdown_content += "\n\n---\n\n".join([f"> {instruction}" for instruction in instructions])

    return markdown_content, image_filename, scraper


def print_markdown(md_content: str) -> None:
    """Prints markdown content with a dynamically limited width.

    Args:
        md_content (str): Markdown content to print.
    """
    clear_console()
    console_width = get_console_width()
    console = Console(width=console_width)
    md = Markdown(md_content)
    console.print("\n", md, "\n")


def save_md_to_file(markdown_content: str, name: str, image_filename: str, scraper: type[AbstractScraper]) -> str:
    """Save recipe Markdown to file and download accompanying image.

    Args:
        markdown_content (str): Markdown content for the recipe.
        name (str): Name of recipe for the metadata and filename.
        image_filename (str): Filename for the accompanying image.
        scraper (AbstractScraper): Dictionary containing scraped data.

    Returns:
        (str, str): Path to saved markdown file and saved image.
    """
    # Format title, create markdown file
    title = format_title(scraper.title()) if name is None else format_title(name)
    recipe_file = DIRECTORY / f"{title}.md"

    # Download accompanying image
    image_path = DIRECTORY / image_filename
    image_data = requests.get(scraper.image()).content
    with open(image_path, "wb") as image_file:
        image_file.write(image_data)

    with open(recipe_file, "w+") as text_file:
        text_file.write(markdown_content)
    return recipe_file, image_file


@cli.command(help="Scrape a recipe URL and print a markdown-formatted recipe to terminal output.")
@click.argument("recipe_url")
@click.option("--prompt-save", default=True, help="Turn on/off the prompt to save the markdown output to file.")
@click_category
@click_extras
@click_translate
def view(recipe_url: str, prompt_save: bool, name: str, category: str, extras: list[str], translate: bool) -> None:
    """Scrape a recipe URL and print a markdown-formatted recipe to terminal output.

    Args:
        recipe_url (str): A URL string from a recipe website.
        prompt_save (bool): Whether to prompt the user to save the recipe.
        name (str): Name of recipe for the metadata and filename.
        category (str): Category in which the recipe belongs.
        extras (list[str]): Extra tags for the recipe (among veggie, spicy, sweet, salty, sour, bitter, and umami).
        translate (bool): Flag on whether to translate the recipe using Google Translate.
    """
    try:
        md_content, image_filename, scraper = generate_markdown(recipe_url, name, category, extras, translate)
        print_markdown(md_content)

        if prompt_save:
            after_view_question = [
                inquirer.List(
                    "after_view",
                    message="What would you like to do next?",
                    choices=["Save this recipe", "Quit"],
                )
            ]

            after_view_answer = inquirer.prompt(after_view_question)
            if after_view_answer["after_view"] == "Save this recipe":
                try:
                    save_md_to_file(md_content, name, image_filename, scraper)
                    logger.info("Recipe saved successfully.")
                except Exception as e:
                    logger.error(f"Error saving the recipe: {str(e)}")
            elif after_view_answer["after_view"] == "Quit":
                return
    except OSError as e:
        logger.error(f"I/O error({e.errno}): {e.strerror}")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}\n")


@cli.command(help="Scrape recipe from URL, parse to Markdown and save to file.")
@click.argument("recipe_url")
@click_name
@click_category
@click_extras
@click_translate
def save(recipe_url: str, name: str, category: str, extras: list[str], translate: bool) -> None:
    """Scrape recipe from URL, parse to Markdown and save to file.

    Args:
        recipe_url (str): URL of the recipe to scrape.
        name (str): Name of recipe for the metadata and filename.
        category (str): Category in which the recipe belongs.
        extras (list[str]): Extra tags for the recipe (among veggie, spicy, sweet, salty, sour, bitter, and umami).
        translate (bool): Flag on whether to translate the recipe using Google Translate.
    """
    md_content, image_filename, scraper = generate_markdown(recipe_url, name, category, extras, translate)
    save_md_to_file(md_content, name, image_filename, scraper)


if __name__ == "__main__":
    cli()
