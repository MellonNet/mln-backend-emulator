# mln-backend-emulator
A server for the MLN social network / game hybrid.

## Requirements:
* Python >= 3.6
* Django >= 2.2
* Pillow library
* (Flash player plugin in the browser)

## Installation

[Install Python and Django](https://docs.djangoproject.com/en/2.1/intro/install/). Install Pillow (`pip install Pillow`).

Download this repository and place it where you like.
Download the MLN content files - to avoid problems with copyright, they aren't included or linked here, but it should be possible to find them if you ask someone involved in the MLN recreation effort.
Place the content folder in `mlnserver/static/`, so that the editorial XML file should be at `mlnserver/static/editorial-redux-v5.xml`.

## Server setup

Initialize the database by running `python manage.py migrate`. This will create the database tables.

Included in the content files should be an XML file called `editorial-redux-v5.xml`. Run `python manage.py import_mln_xml <path>`, where <path> is the path to this file. This will import the original MLN data.

Note: The editorial XML unfortunately doesn't contain any information about networkers. This means that the server won't have any networkers, even after importing the MLN data. We're trying to piece together networker information ourselves, using the MLN wiki and screenshots of pages. However this information is likely incomplete, so while we may be able to reconstruct networkers to the point where you can achieve all ranks, we probably won't be able to get the layout of the modules on their pages completely correct. Once we've completed piecing together the networker data we'll also make this data available to you if you want to host your own server.

## Run the server

Run the server with `python manage.py runserver` (the option ` --noreload` can be used to disable automatic file scanning which can significantly improve performance).

The MLN private view should be available at http://localhost:8000/mln/private_view/default. The server also works with Django's admin interface, which should be available at http://localhost:8000/admin/.

Do *not* use this way of running the server in production (if you actually want the server to be available to untrusted users over the network). [Here](https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/)'s a list of things to do before deploying the server in production, and [here](https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/)'s how to run the server with an actual dedicated web server using WSGI.

## Features
### Implemented
* Private view
	* Inventory
		* Blueprints
		* Masterpieces
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
* Networker friendship conditions


### Not yet implemented
* Networker mail replies
* Random items sometimes sent to friends when you click on modules
* Items guests can receive in "battle" modules or similar
* Module-dependent sticker backgrounds
* Statistics
	* Module stats
	* Arcade stats
* Creation lab category & download link
* Factory "check price" link

## Disclaimer
LEGO<sup>Ⓡ</sup> is a trademark of the LEGO Group. The LEGO Group is not affiliated with CollectNet, has not endorsed or authorized its operation, and is not liable for any safety issues in relation to its operation.

The operation of this project follows existing precedents and guidelines set by the LEGO Group (and other organizations) in relation to fan projects and abandonware (including the existance of other such projects). Should any party with claim to the intillectual property used in this project have issue with its operation, action will be taken as soon as possible upon contact to make adjustments or ultimately remove this project if necessary.
