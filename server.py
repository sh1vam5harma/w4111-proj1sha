
"""
#test comment
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
import psycopg2
import random
import string
from datetime import date

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@34.73.36.248/project1
#
# For example, if you had username zy2431 and password 123123, then the following line would be:
#
#     DATABASEURI = "postgresql://zy2431:123123@34.73.36.248/project1"
#
# Modify these with your own credentials you received from TA!
DATABASE_USERNAME = "ss6454"
DATABASE_PASSWRD = "5575"
DATABASE_HOST = "34.148.107.47" # change to 34.28.53.86 if you used database 2 for part 2
DATABASEURI = f"postgresql://ss6454:5575@34.148.107.47/project1"




#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
with engine.connect() as conn:
	create_table_command = """
	CREATE TABLE IF NOT EXISTS test (
		id serial,
		name text
	)
	"""
	res = conn.execute(text(create_table_command))
	insert_table_command = """INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace')"""
	res = conn.execute(text(insert_table_command))
	# you need to commit for create, insert, update queries to reflect
	conn.commit()


@app.before_request
def before_request():
	"""
	This function is run at the beginning of every web request 
	(every time you enter an address in the web browser).
	We use it to setup a database connection that can be used throughout the request.

	The variable g is globally accessible.
	"""
	try:
		g.conn = engine.connect()
	except:
		print("uh oh, problem connecting to database")
		import traceback; traceback.print_exc()
		g.conn = None

@app.teardown_request
def teardown_request(exception):
	"""
	At the end of the web request, this makes sure to close the database connection.
	If you don't, the database could run out of memory!
	"""
	try:
		g.conn.close()
	except Exception as e:
		pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: https://flask.palletsprojects.com/en/1.1.x/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
	"""
	request is a special object that Flask provides to access web request information:

	request.method:   "GET" or "POST"
	request.form:     if the browser submitted a form, this contains the data in the form
	request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

	See its API: https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data
	"""

	# DEBUG: this is debugging code to see what request looks like
	print(request.args)


	#
	# example of a database query
	#
	select_query = "SELECT r.last_name, r.first_name, reg.finish_time -reg.start_time AS elapsed_time FROM runner r JOIN registration reg ON r.runner_id = reg.runner_id JOIN race ra ON ra.race_id = reg.race_id WHERE ra.race_name = 'nyc_marathon' AND reg.completed = 'Y'"
	cursor = g.conn.execute(text(select_query))
	names = []
	for result in cursor:
		names.append(result)
	cursor.close()

	#
	# Flask uses Jinja templates, which is an extension to HTML where you can
	# pass data to a template and dynamically generate HTML based on the data
	# (you can think of it as simple PHP)
	# documentation: https://realpython.com/primer-on-jinja-templating/
	#
	# You can see an example template in templates/index.html
	#
	# context are the variables that are passed to the template.
	# for example, "data" key in the context variable defined below will be 
	# accessible as a variable in index.html:
	#
	#     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
	#     <div>{{data}}</div>
	#     
	#     # creates a <div> tag for each element in data
	#     # will print: 
	#     #
	#     #   <div>grace hopper</div>
	#     #   <div>alan turing</div>
	#     #   <div>ada lovelace</div>
	#     #
	#     {% for n in data %}
	#     <div>{{n}}</div>
	#     {% endfor %}
	#
	context = dict(data = names)


	#
	# render_template looks in the templates/ folder for files.
	# for example, the below file reads template/index.html
	#
	return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
@app.route('/another')
def another():
    print(request.args)
    select_query = "SELECT * FROM training_program;"
    cursor = g.conn.execute(text(select_query))
    names = []
    for result in cursor:
        names.append(result)
    cursor.close()
    context = dict(data = names)
    return render_template("another.html", **context)


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
	# accessing form inputs from user
	name = request.form['name']
	
	# passing params in for each variable into query
	params = {}
	params["new_name"] = name
	g.conn.execute(text('INSERT INTO test(name) VALUES (:new_name)'), params)
	g.conn.commit()
	return redirect('/')



@app.route('/log_training_event', methods=['GET', 'POST'])
def log_training_event():
    
    if request.method == 'POST':
        # Get user input from the form
        py_training_type = request.form['training_type']
        py_date = request.form['date']
        py_start = request.form['start_time']
        py_finish = request.form['finish_time']
        py_miles = request.form['miles']
        py_runner_id = request.form['runner_id']
        #insert_table_command = """INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace')"""
	#res = conn.execute(text(insert_table_command))
	# you need to commit for create, insert, update queries to reflect
	#conn.commit()

        # Generate a random event_id
        py_event_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        #training_event = [(training_type1, date1, start1, finish1, miles1, event_id)]
        # Insert the new training event into the training_event table
        insert_command = "INSERT INTO training_event(training_type, date, start, finish, miles, event_id) VALUES (?, ?, ?, ?, ?, ?)"
        values1 = (py_training_type, py_date, py_start, py_finish, py_miles, py_event_id)
        res = g.conn.execute(insert_command, values1)
        #g.conn.execute("INSERT INTO training_event(training_type, date, start, finish, miles, event_id) VALUES (?, ?, ?, ?, ?, ?)", (py_training_type, py_date, py_start, py_finish, py_miles, py_event_id))
        #cursor.execute("INSERT INTO training_event (training_type, date, start, finish, miles, event_id) VALUES (%s, %s, %s, %s, %s, %s)", (training_type, date, start, finish, miles, event_id))
        g.conn.commit()
        res.close()
        #conn.close()
        # Insert the new log entry into the log table
        log_insert_command = "INSERT INTO log(runner_id, event_id) VALUES (?, ?)"
        values2 =(py_runner_id, py_event_id)
        #g.conn.execute("INSERT INTO log(runner_id, event_id) VALUES (?, ?)", (py_runner_id, py_event_id))
        res2 = g.conn.execute(log_insert_command, values2)

        g.conn.commit()
        #cursor.execute("INSERT INTO log (runner_id, event_id) VALUES (%s, %s)", (runner_id, event_id))
        
        res2.close()
        #g.conn.commit()
        #cursor.close()
        #conn.close()
        return "Training event added successfully!"

    else:
        return  render_template('log_training_event.html')

def index():

# Establish a connection to tihe database
	conn = psycopg2.connect(DATABASEURI)

# Create a cursor object
	cursor = conn.cursor()


	cursor.execute("""
	    SELECT r.last_name, r.first_name, reg.finish_time - reg.start_time AS elapsed_time
	    FROM runner r
	    JOIN registration reg ON r.runner_id = reg.runner_id
	    JOIN race ra ON ra.race_id = reg.race_id
	    WHERE ra.race_id = '1' AND reg.completed = 'Y'
	""")


	results = cursor.fetchall()

	conn.close()
	return render_template('index.html', results=results)



@app.route('/runner_name', methods=['GET', 'POST'])
def add_volunteer():
    if request.method == 'POST':
        # Accessing form inputs from user
        volunteer_id = request.form.get('volunteer_id')
        last_name = request.form.get('last_name')
        first_name = request.form.get('first_name')
        gender = request.form.get('gender')
        email = request.form.get('email')
        date_of_birth = request.form.get('date_of_birth')

        # Establish connection to database
        conn = psycopg2.connect(DATABASEURI)
        cursor = conn.cursor()

        # Insert the new volunteer into the database
        cursor.execute("INSERT INTO VOLUNTEER (VOLUNTEER_ID, LAST_NAME, FIRST_NAME, GENDER, EMAIL, DATE_OF_BIRTH) VALUES (?, ?, ?, ?, ?, ?)",
                       (volunteer_id, last_name, first_name, gender, email, date_of_birth))

        # Commit the changes to the database
        conn.commit()

        # Close the database connection
        cursor.close()
        conn.close()

        # Redirect to the homepage
        return redirect('/')
    else:
        return render_template('runner_name.html')







@app.route('/login')
def login():
	abort(401)
	this_is_never_executed()


if __name__ == "__main__":
	import click

	@click.command()
	@click.option('--debug', is_flag=True)
	@click.option('--threaded', is_flag=True)
	@click.argument('HOST', default='0.0.0.0')
	@click.argument('PORT', default=8111, type=int)
	def run(debug, threaded, host, port):
		"""
		This function handles command line parameters.
		Run the server using:

			python server.py

		Show the help text using:

			python server.py --help

		"""

		HOST, PORT = host, port
		print("running on %s:%d" % (HOST, PORT))
		app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

run()
