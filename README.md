# Let's Go There - A FastAPI app for a shared travel bucket list

This is the backend for a web app that allows users to create joint lists of places they'd like to visit and attractions they'd like to see. A typical use case could be a couple planning a 'bucket list' of future holiday destinations. It could also be used by groups of individuals jotting down ideas for things to do on an upcoming trip.

## Features

* Sign in using Google (OIDC)
* Create a list of travel ideas
* Invite other people to your list using their email address
* Add travel ideas to any list you're a member of
* Accept or reject invitations to lists owned by other users

## Technologies

* FastAPI / Python
* SQLAlchemy
* Alembic
* Pytest
* UV
* Ruff

## How this could be extended

* Build a frontend(!), to include features such as:
    - Allow users to pin their travel ideas on a map (e.g. via integration with Google Maps)
    - Give users the ability to choose an image for each travel idea (e.g. using the Unsplash API)
* Notify users of new list invitations via email using a service such as Mailgun
