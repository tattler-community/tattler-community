# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'tattler'
copyright = '2023 - 2024, tattler.dev'
author = 'Michele Mazzucchi, keencons.com'
release = '2.0.0'

language = 'en'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autosectionlabel",
    "sphinxcontrib.mermaid",
    "sphinx.ext.autodoc",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
    "sphinxcontrib.googleanalytics",
]

# make sphinx-copybutton skip all prompt characters generated by pygments, use the following setting
copybutton_exclude = '.linenos, .gp'

# Make sure the target is unique
autosectionlabel_prefix_document = True


templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = 'alabaster'
html_theme = "furo"
html_static_path = ['_static']

html_favicon = 'tattler-favicon.png'
# the "furo" theme allows setting different logos for light and dark mode

# LOGO

# Use either of the following 2 options:
#
# A) one generic logo. Pros and contras:
#   + works natively in Sphinx, regardless of the theme
#   + sphinx automatically copies the logo file into the build directory
#   + only one logo to manage
#   + simpler configuration
#   - resulting logo might display suboptimally on light/dark mode
#
# B) custom logos for light and dark modes
#   + displays perfectly in each mode
#   - more complex configuration
#   - theme-specific

# For option A, uncomment the following: (see https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_logo)
##html_logo = 'tattler-logo-small-colorneutral.png'

# For option B, uncomment the following: (see https://pradyunsg.me/furo/customisation/logo/)
#html_static_path = ["_static"]
html_theme_options = {
    "light_logo": "tattler-logo-small-light.png",
    "dark_logo": "tattler-logo-small-dark.png",
}
html_extra_path = ['tattler-logo-small-dark.png', 'tattler-logo-small-light.png']

# google analytics
googleanalytics_id = 'G-TBG7MQ2X2H'
