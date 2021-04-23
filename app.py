from flask import Flask, render_template, request, redirect, url_for
from sense_hat import SenseHat 
import sqlite3 
from flask_apscheduler import APScheduler
import time


sense = SenseHat()
sense.low_light = True


app = Flask(__name__)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


@app.route('/', methods=['GET','POST'])
def index():
    #connect to database
    conn = sqlite3.connect('./static/data/toDos.db')
    curs = conn.cursor()

    todos = []
    
    if request.method == 'GET':
       todos = get_all_todos(curs, 'pending')
    else: 
        #get posted form data using names assigned in HTML
        todo = request.form['reminder']
        deadline = request.form['time']
        status = "pending"
        curs.execute("INSERT INTO todos (todo, deadline, status) VALUES ((?), (?), (?))", (todo, deadline, status))
        conn.commit()
        todos = get_all_todos(curs, 'pending')
    done = get_total_todos(curs, 'done')
    #close database connection
    conn.close()
    return render_template('index.html', to_dos = todos, done=done)    

@app.route('/reminder/<action>/<id>', methods=['GET','POST'])
def edit(action, id):
    #connect to database
    conn = sqlite3.connect('./static/data/toDos.db')
    curs = conn.cursor()
    str_id = str(id)
    if action == 'delete':
        curs.execute("DELETE FROM todos WHERE rowid=(?)", (id,))
        if(scheduler.get_job(str_id)):
            scheduler.remove_job(str_id)
    elif action == 'complete':
        curs.execute("UPDATE todos SET status=(?) WHERE rowid=(?)", ('done',id))
        if(scheduler.get_job(str_id)):
            scheduler.remove_job(str_id)
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/all')
def all():
    todos = get_all_todos(curs, 'all') 
    return render_template('index.html', to_dos = todos)    

def get_all_todos(curs, status):
    todos = []
    rows = ''
    if status == 'all':
        rows = curs.execute("SELECT rowid, todo, deadline from todos ORDER BY deadline ASC")
    else:
        rows = curs.execute("SELECT rowid, todo, deadline from todos WHERE status=(?) ORDER BY deadline ASC", ("pending",))
    for row in rows:
        todo = {'id': row[0], 'todo': row[1], 'deadline':row[2]}
        todos.append(todo)
        #Schedule task - tasks already scheduled will be ignored
        if(not scheduler.get_job(str(todo['id']))):
            scheduler.add_job(id=str(todo['id']), func=give_reminder, trigger='date', run_date=todo['deadline'], args=[todo['todo']])
    return todos

def get_total_todos(curs, status):
    if status=='done':
        count = curs.execute("SELECT COUNT(*) FROM todos WHERE status=(?)", ("done",)).fetchone()[0]
    return count

def give_reminder(todo):
    sense.show_message(todo)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
    
    

