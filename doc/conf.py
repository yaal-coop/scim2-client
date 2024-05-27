import datetime
import os
import sys
from importlib import metadata

sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath("../httpx_scim_client"))

# -- General configuration ------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.doctest",
    "sphinx.ext.graphviz",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
master_doc = "index"
project = "httpx-scim-client"
year = datetime.datetime.now().strftime("%Y")
copyright = f"{year}, Yaal Coop"
author = "Yaal Coop"
source_suffix = {
    ".rst": "restructuredtext",
    ".txt": "markdown",
    ".md": "markdown",
}

version = metadata.version("httpx_scim_client")
language = "en"
exclude_patterns = []
pygments_style = "sphinx"
todo_include_todos = True
toctree_collapse = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pydantic_scim2": ("https://pydantic-scim2.readthedocs.io/en/latest/", None),
}

# -- Options for HTML output ----------------------------------------------

html_theme = "shibuya"
# html_static_path = ["_static"]
html_baseurl = "https://httpx-scim-client.readthedocs.io"
html_theme_options = {
    "globaltoc_expand_depth": 3,
    "accent_color": "lime",
    "github_url": "https://github.com/yaal-coop/httpx-scim-client",
    "mastodon_url": "https://toot.aquilenet.fr/@yaal",
    "nav_links": [
        {
            "title": "SCIM",
            "url": "https://simplecloud.info/",
            "children": [
                {
                    "title": "RFC7642 - SCIM: Definitions, Overview, Concepts, and Requirements",
                    "url": "https://tools.ietf.org/html/rfc7642",
                },
                {
                    "title": "RFC7643 - SCIM: Core Schema",
                    "url": "https://tools.ietf.org/html/rfc7643",
                },
                {
                    "title": "RFC7644 - SCIM: Protocol",
                    "url": "https://tools.ietf.org/html/rfc7644",
                },
            ],
        },
        {"title": "pydantic-scim2", "url": "https://pydantic-scim2.readthedocs.io"},
        {
            "title": "scim-cli",
            "url": "https://scim-cli.readthedocs.io",
        },
    ],
}

# -- Options for manual page output ---------------------------------------

man_pages = [
    (master_doc, "httpx-scim-client", "httpx-scim-client Documentation", [author], 1)
]

# -- Options for Texinfo output -------------------------------------------

texinfo_documents = [
    (
        master_doc,
        "httpx_scim_client",
        "httpx_scim_client Documentation",
        author,
        "httpx_scim_client",
        "One line description of project.",
        "Miscellaneous",
    )
]

# -- Options for autosectionlabel -----------------------------------------

autosectionlabel_prefix_document = True
autosectionlabel_maxdepth = 2
