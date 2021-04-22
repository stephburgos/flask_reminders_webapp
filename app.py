from flask import Flask, render_template, request, redirect, url_for
from sense_hat import SenseHat 
import sqlite3 

sense = SenseHat()
sense.low_light = True

app = Flask(__name__)

@app.route('/', methods=['GET','POST'])
def index():
    #connect to database
    conn = sqlite3.connect('./static/data/toDos.db')
    curs = conn.cursor()

    todos = []
    
    if request.method == 'GET':
       todos = getAllTodos(curs, 'pending')
    else: 
        #get posted form data using names assigned in HTML
        todo = request.form['reminder']
        deadline = request.form['time']
        status = "pending"
        curs.execute("INSERT INTO todos (todo, deadline, status) VALUES ((?), (?), (?))", (todo, deadline, status))
        conn.commit()
        todos = getAllTodos(curs)
    #close database connection
    conn.close()
    return render_template('index.html', to_dos = todos)    

@app.route('/reminder/<action>/<id>', methods=['GET','POST'])
def edit(action, id):
    #connect to database
    conn = sqlite3.connect('./static/data/toDos.db')
    curs = conn.cursor()
    if action == 'delete':
        curs.execute("DELETE FROM todos WHERE rowid=(?)", (id,))
    elif action == 'complete':
        curs.execute("UPDATE todos SET status=(?) WHERE rowid=(?)", ('done',id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/all')
def all():
    todos = getAllTodos(curs, 'all') 
    return render_template('index.html', to_dos = todos)    

def getAllTodos(curs, status):
    todos = []
    rows = ''
    if status == 'all':
        rows = curs.execute("SELECT rowid, todo, deadline from todos ORDER BY deadline ASC")
    else:
        rows = curs.execute("SELECT rowid, todo, deadline from todos WHERE status=(?) ORDER BY deadline ASC", ("pending",))
    for row in rows:
        todo = {'id': row[0], 'todo': row[1], 'deadline':row[2]}
        todos.append(todo)
    return todos

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
    
    

