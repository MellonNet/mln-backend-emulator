# mln-backend-emulator
## Running the server

### Static files

The files behind My Lego Network were split into two categories:

1. Front-end Flash files that were sent to the browser
2. Back-end files and data that were kept on the server

We were able to recover the frontend files, but to avoid copyright infringement, we will not post them here. Those need to be downloaded separately and placed into the `static` folder. Specifically, you should have a file `static/editorial-redux-v6.xml` that is needed for everything to work.

This repository is a recreation of the backend server logic. It will handle network requests from the Flash code and serve the responses they are expecting, but it is not possible to change the Flash logic from here. We are looking to possibly rewrite the frontend to allow it to run on modern browsers and have a cleaner API.

### First time setup

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py import_mln_xml static/editorial-redux-v6.xml
python manage.py createsuperuser
```

The super user account can be used to manage the database, but you can still make separate accounts for your MLN profiles. **There is no information about networkers in the editorial XML file, so after running these commands you will still need to create them yourself.** We have already hand-filled this data on our server and are working on an export and import feature.

If you need to test a feature with networkers, go to the sign up page to make them an account. Now you can manage them and their data in the Django admin portal (see the next section). First be sure go into their `Profile` and check off the `is_networker` box. Then you can add other associated information, like Networker friendship conditions.

### Run the server

```bash
python manage.py runserver
```

This command will watch your file system for changes and automatically reload the server. For development, this is useful, but if you're just running the server and need more performance, use the `--noreload` option.

The MLN site should be available at http://localhost:8000. You can sign in with your super user account from earlier, or use the sign up page to create a new account. Note that if you want Echo to automatically friend you you must create a new profile after adding Echo to the database.

The Django admin interface should be available at http://localhost:8000/admin. Here you can view the database and make changes to any item. These will usually affect the MLN site after a reload, and will require you to be signed in with your super user account.

Do *not* use this way of running the server in production (if you actually want the server to be available to untrusted users over the network). [Here](https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/)'s a list of things to do before deploying the server in production, and [here](https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/)'s how to run the server with an actual dedicated web server using WSGI.

## Features

### Fully working
- Private view and all sub-pages
- Public view and module interactions
- Full progression from start to Rank 10
- Gallery, Factory, and Creation Lab
- Sign in with My Lego Network, see [oauth.md](./oauth.md)

### Wishlist
- A database export/import feature (see https://github.com/MellonNet/mln-backend-emulator/pull/31)
- Networkers can click on your modules when you send them click requests
- Mini-game integrations (Lego City Coast Guard coming soon!)
- Consolidating messages when the same body/attachments are sent
- Some sort of moderation, possibly involving Dead Letter Postman
- Private page statistics
- A full rework of the front-end to work on modern browsers

### Not going to be implemented

- Echo's code module. it only works on one code, and that code is hard-coded into the module's Flash code.

## Disclaimer
LEGO<sup>Ⓡ</sup> is a trademark of the LEGO Group. The LEGO Group is not affiliated with MellonNet, has not endorsed or authorized its operation, and is not liable for any safety issues in relation to its operation.

The operation of this project follows existing precedents and guidelines set by the LEGO Group (and other organizations) in relation to fan projects and abandonware (including the existance of other such projects). Should any party with claim to the intillectual property used in this project have issue with its operation, action will be taken as soon as possible upon contact to make adjustments or ultimately remove this project if necessary.
