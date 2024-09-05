import os
import re
import shutil
import textwrap
from pathlib import Path

import click
import inquirer
import requests
from loguru import logger
from recipe_scrapers import scrape_me
from rich.console import Console
from rich.markdown import Markdown

DIRECTORY = Path("./local/")

console = Console()


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


def format_file_name(recipe_title: str) -> str:
    """Convert the recipe title to a nice format.

    Args:
        recipe_title (str): a string containing a recipe title.
    Returns:
        str: formatted title
    """
    s = list(recipe_title.lower())

    for i, char in enumerate(s):
        if char.isspace():
            s[i] = "-"
    return "".join(s)


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


def generate_markdown(recipe_url: str) -> (str, str, dict):
    """Given a recipe URL, scrape and generate the markdown content.

    Args:
        recipe_url (str): url string from a recipe website.

    Returns:
        (str, str, dict): Markdown content for the recipe, image filename and scraped data dictionary.
    """
    try:
        scraper = scrape_me(recipe_url)
    except Exception as e:
        logger.error(f"Could not scrape recipe, error: {str(e)}")
        return "", "", {}

    # Format title
    title = format_title(scraper)
    # Download accompanying image
    image_file_extension = scraper.image().split(".")[-1]
    image_filename = f"{format_file_name(title)}.{image_file_extension}"

    markdown_content = ""
    markdown_content += textwrap.dedent(f"""\
            ---
            title: {title.replace('-', ' ')}
            category: XXX
            source: {recipe_url}
            image: {image_filename}
            size: {scraper.yields()}
            time: {scraper.total_time()}
            nutrition:""")
    # Nutrition components
    for nutrient, quantity in scraper.nutrients().items():
        markdown_content += f"\t{camel_case_splitter(nutrient).replace(' content', '')} {quantity}\n"
    markdown_content += "---\n"
    # Print all ingredients
    for ingredient in scraper.ingredients():
        markdown_content += f"* {ingredient}\n"
    # Print all instructions
    for instruction in scraper.instructions_list():
        markdown_content += "\n---\n"
        markdown_content += f"> {instruction}"

    return markdown_content, image_filename, scraper


def save_md_to_file(markdown_content: str, image_filename: str, scraper: dict) -> str:
    """Save recipe Markdown to file and download accompanying image.

    Args:
        markdown_content (str): Markdown content for the recipe.
        image_filename (str): Filename for the accompanying image.
        scraper (dict): Dictionary containing scraped data.

    Returns:
        (str, str): Path to saved markdown file and saved image.
    """
    # Format title, create markdown file
    title = format_title(scraper)
    recipe_file = DIRECTORY / f"{format_file_name(title)}.md"

    # Download accompanying image
    image_path = DIRECTORY / image_filename
    image_data = requests.get(scraper.image()).content
    with open(image_path, "wb") as image_file:
        image_file.write(image_data)

    with open(recipe_file, "w+") as text_file:
        text_file.write(markdown_content)
    return recipe_file, image_file


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


@cli.command()
@click.argument("recipe_url")
@click.option("--prompt-save", default=True, help="Turn on/off the prompt to save the markdown output to file.")
def view(recipe_url: str, prompt_save: bool = True) -> None:
    """Scrape a recipe URL and print a markdown-formatted recipe to terminal output.

    Args:
        recipe_url (str): A URL string from a recipe website.
        prompt_save (bool, optional): Whether to prompt the user to save the recipe. Defaults to True.
    """
    try:
        md_content, image_filename, scraper = generate_markdown(recipe_url)
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
                    save_md_to_file(md_content, image_filename, scraper)
                    logger.info("Recipe saved successfully.")
                except Exception as e:
                    logger.error(f"Error saving the recipe: {str(e)}")
            elif after_view_answer["after_view"] == "Quit":
                return
    except OSError as e:
        logger.error(f"I/O error({e.errno}): {e.strerror}")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}\n")


@cli.command()
@click.argument("recipe_url")
def save(recipe_url: str) -> None:
    """Scrape recipe from URL, parse to Markdown and save to file

    Args:
        recipe_url (str): URL of the recipe to scrape.
    """
    md_content, image_filename, scraper = generate_markdown(recipe_url)
    save_md_to_file(md_content, image_filename, scraper)


if __name__ == "__main__":
    cli()
