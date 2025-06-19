# Accounts
This is a simple webservice that simulates a banking experience.

No AI tooling has been used when writing this project.

## The Problem
The problem here is to write a web service, which allows you to create a few 'bank' accounts and then transfer funds between them.

## The Solution
The solution to the above problem has been to write a simple REST API written as a web service with Python 3 using the flask library.
Python was chosen, as my focus was to build something quickly and Python allows you to do that.

The solution has not been deployed anywhere and only consists of the web service. So interaction happens exclusivly via a REST API on a local machine.

The imgained user flow for the application is:

`Create new user -> Authenticate -> Create Account -> Transfer funds to another account`.

### API
The API itself is based around the REST paradigm. This in part means that we are working with stateless requests. 
The server doesn't store any session data about what a user has done previously, all state data must be provided in the request. 
This makes our backend a lot simpler, as we don't need to manage any session state.

If you would like to see the API endpoints in postman you can import the  `Accounts.postman_collection.json` collection file found in this repository.
Otherwise, reading the routes in `app.py` should give you a good idea of what endpoints are available.

### Architecture
The code base is designed with this architectural hierachy in mind `API-Layer -> Business-Layer -> Store`.
That is, the API layer, found in `app.py` can only call into the Business-Layer, represented by the `UserCollection` and `AccountCollection` classes.
In turn the Business-Layer can only call into the Store, represented by the `UserStore` and `AccountStore`. This ensures that there is some seperation of concern.

Both `*Store` classes are abstract and need implementations. With the time given, I've implemented these using in-memory python lists in `InMemoryUserStore` and `InMemoryAccountStore`. 
The downside of this is that our data is not persisted, once the service shuts down. However since the store logic is hidden behind an abstract class, it should be relativly simple to write some new stores that use some external database, for example mongoDB.

### Error Handling
All custom errors that we raise inherit from the `ApiError` class. These errors include API-level details like status codes and are meant to hit the user at the API-level. This also means that one should be careful not to include sensitive data in them, as it could be displayed to the user.
Errors that we don't raise ourselves will at the API-level be interpreted by flask as `500 Internal Server` errors and logged as such.

### Logging
Regular logs are currently just streamed to the console. If I were to send this to production it should be logged to a file instead. That logging file should then be ingested into a tool like Humio for storage and search. 
I've taken care to include relevant information in each log depending on context.
As for logging levels, my decision has been to only use `ERROR` for fault situations we would need to alert on. Otherwise faulty behaviour is logged with a `Warning`.

### Audit
Auditing has been implemented as a separate logger `audit`. Using this logger will write an audit log to the `audit.log` file, which in principle could be sent off to an auditer. But again, I'd probably stick this into something like Humio first to not have it stored on a local machine.

### Testing
The project implements some Class level testing of the `UserCollection` and `AccountCollection` classes, as these include most of the business logic of the application.
To run all tests just run the `pytest` command in the command line.

For API-level testing, I might deploy this on a test server and then use something like Postman for creating some test runs.

## Running The Service
I have only tested this on my machine, but if you have Python 3 installed, running this should be as simple as:
1. Cloning this repository to your own machine
2. Creating a Python virtualenv in the repo directory
3. Running `pip install -r requirements.txt` to install all needed libraries
4. Create a config.json file with the following keys `JWT_SECRET_KEY`, `JWT_TOKEN_LOCATION` and `JWT_ACCESS_TOKEN_EXPIRES`
6. Run `flask run`

Then you should have the web server running on `http://localhost:5000`.

## Next Steps
These are some imaginary next steps for if I were to spend some more time on this.

### Persistence
As noted, data is currently not persisted within the application. So I'd implement some `MongoUserStore` and `MongoAccountStore` classes to interact with a MongoDB instance for production use.
Calls to mongo would be async, so that would also require some thought into how to handle outgoing async calls in the application.

### Deletion
Currently users and accounts cannot be deleted, which makes the application logic rather simple. For instance, if I have a valid JWT token with a `user_id` I know for certain that the user will exist.
Adding deletion would require handling the case where the user a JWT belongs to has been deleted. 

### Frontend
Most humans don't like to interact with applications through a REST API so I would have to create a frontend. Flask can actually serve (HTML, CSS, JS) to the caller, so it should be possible to make a very simple old-school frontend for this.

### Deployment
By design a flask application runs as a single process, handling requests sequentially. So you wouldn't want to run the application on its own in production.
Instead you could run it on WSGI server, which can spawn multiple processes depending on demand. Alternativly the application could be included in a docker image, and then multiple container instances could be run within a container service like AWS ECS.
