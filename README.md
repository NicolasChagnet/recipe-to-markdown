# Recipe to Markdown

This is a fork of the excellent [Pure Recipe](https://github.com/atiumcache/pure-recipe) CLI application which scrapes common recipe websites and formats them to Markdown files. The goal of this fork is to make the markdown output compatible with the [Nyum recipe manager](https://github.com/doersino/nyum) which converts Markdown files to a static website.

- [Recipe to Markdown](#recipe-to-markdown)
	- [Features](#features)
	- [Installation](#installation)
	- [Usage](#usage)
		- [View in Terminal](#view-in-terminal)
		- [Save to Markdown](#save-to-markdown)
	- [Supported Websites](#supported-websites)
	- [Troubleshooting](#troubleshooting)
	- [Future Work](#future-work)
	- [Contributing](#contributing)
	- [License](#license)

## Features

- View recipes directly in your terminal.
- Save recipes to markdown for easy access and sharing.
- Support for a wide range of cooking sites.
- Easy-to-use command-line interface.
- Translate recipes to English automatically.
- Format Markdown recipes in a format compatible with the Nyum recipe manager.

## Installation

**Pre-requisites:**

- Python 3.10 or higher.

**Steps:**

1. Clone the repository or download one of the binaries in the `dist/` folder.
2. Install the required Python dependencies:
```bash	
pip install .
```


## Usage

There are currently two options: `view` or `save`. Both admit various customization options as highlighted in the help section:
```
Usage: recipe2md view [OPTIONS] RECIPE_URL

  Scrape a recipe URL and print a markdown-formatted recipe to terminal
  output.

Options:
  --prompt-save BOOLEAN           Turn on/off the prompt to save the markdown
                                  output to file.
  -c, --category TEXT             Category in which the recipe belongs.
  -e, --extra [veggie|spicy|sweet|salty|sour|bitter|umami]
                                  Extra tags for the recipe (among veggie,
                                  spicy, sweet, salty, sour, bitter, and
                                  umami).
  -t, --translate                 Translate the content of the recipe using
                                  Google Translate.
  -o, --out DIRECTORY             Folder where the output files are to be
                                  stored.
  --help                          Show this message and exit.
```

### View in Terminal

**Command:**
```bash
python recipe2md.py view [RECIPE_URL]
```

**Example:**
```bash
python recipe2md.py view https://www.seriouseats.com/potato-wedges-recipe-5217319
```

### Save to Markdown

**Command:**
```bash
python recipe2md.py save [RECIPE_URL]
```

**Example:**
```bash
python recipe2md.py save https://www.seriouseats.com/potato-wedges-recipe-5217319
```

Saves a recipe from a given URL, as well as the default picture associated with the recipe. The default save location is the current folder but can be changed using the `--out/-o` option.


## Supported Websites

Check out the [list of supported websites](https://github.com/hhursev/recipe-scrapers#scrapers-available-for) for recipe scraping.

## Troubleshooting

- Dependency Issues: Ensure all dependencies are correctly installed.
- Invalid URLs: Check the URL format and website support.
- File Permissions: Ensure you have write permissions to the specified recipe directory.

## Future Work

- Allow for configuration

## Contributing

Contributions are welcome! If you have a suggestion or want to contribute code, please feel free to make a pull request or open an issue.

## License

Distributed under the MIT License. See LICENSE.txt for more information.
