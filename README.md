# mlnserver
## A server for the MLN social network / game hybrid.
### Created by lcdr
### Source repository at https://bitbucket.org/lcdr/mlnserver/
### License: [AGPL v3](https://www.gnu.org/licenses/agpl-3.0.html)

#### Requirements:
* Python >= 3.6
* Django >= 2.1
* Pillow library
* (Flash player plugin in the browser)

### Installation

[Install Python and Django](https://docs.djangoproject.com/en/2.1/intro/install/). Install Pillow (`pip install Pillow`).

Download this repository and place it where you like.
Download the MLN content files - to avoid potential problems with copyright, they aren't included in the repo nor linked here, but it should be possible to find them if you search the web or ask someone involved in the MLN recreation effort.
Place the content folder in a directory specified by `STATICFILES_DIRS` in `mlnserver/settings.py`. The default is `/content/`, so that the editorial should be at `/content/editorial-redux-v3.xml`.

### Server setup

Initialize the database by running `python manage.py migrate`. This will create the database tables.

Included in the content files should be an XML file called `editorial-redux-v3`. Run `python manage.py import_mln_xml <path>`, where <path> is the path to this file. This will import the original MLN data.

### Run the server

Run the server with `python manage.py runserver` (the option ` --noreload` can be used to disable automatic file scanning which can significantly improve performance). At this point the server should be running at `localhost:8000`.
Do *not* use this way of running the server in production (if you actually want the server to be available to users over the network). [Here](https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/)'s a list of things to do before deploying the server in production, and [here](https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/)'s how to run the server with an actual dedicated web server using WSGI.

The MLN private view should be available at http://localhost:8000/mln/private_view/default. The server also works with Django's admin interface, which should be available at http://localhost:8000/admin/.

### Features
#### Implemented
* Private view
	* Inventory
		* Blueprints
	* Page builder
		* Module customization & configuration
	* Mail
		* Easy replies
		* Attachments
* Public view
	* Modules
		* Item growth & Harvesting
		* Setup & Teardown
		* Voting & Execution
		* Arcade
	* Avatar & About me
	* Badges
	* Page skins & colors
	* Friends & blocked friends
* Gallery & Factory
* Creation lab

#### Not implemented
* Networkers
* Masterpieces
* Random items sometimes sent to friends when you click on modules
* Items guests can receive in "battle" modules or similar
* Some serverside prereq checking
* Module-dependent sticker backgrounds
* Statistics
	* Module stats
	* Arcade stats
* Creation lab category & download link
* Factory "check price" link
