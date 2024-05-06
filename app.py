# app.py
from flask import Flask, render_template, request, jsonify, url_for, redirect, session
# from flask_sock import Sock
from flask_socketio import SocketIO
from flask_cors import CORS
import time, random, json

import mysql.connector

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")
app.config['SOCK_SERVER_OPTIONS'] = {'ping_interval': 25}
app.config['SECRET_KEY'] = 'choy'

# MySQL configuration
mysql_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'quiz'
}


# Define global variables for the timer
time_preferred = 20 # MAO NI ILISI PARA SA TIMER
game_ongoing = False
isHost = 0
Host = None

@app.route('/')
def enter_username():
    try:
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Scores")
        result = cursor.fetchone()

        
        global game_ongoing, Host
        if result is not None:
            return render_template('join.html', status = 'Join', game_ongoing = game_ongoing)
        else:
            game_ongoing = False
            if Host:
                Host = None  
                socketio.emit('update_test','Create')
            return render_template('join.html', status = 'Create', game_ongoing = game_ongoing)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/enter', methods=['POST'])
def index():
    if game_ongoing:
        return redirect("/")

    username = request.form['username']
    if not username.strip():
        return jsonify({'status': 'error', 'message': 'Please enter a username.'}), 400
    try:
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Scores (username, score) VALUES (%s, 0)", (username,))
        conn.commit()
        conn.close()
        
        return redirect(url_for('game', username=username))  # Redirect to index.html with username
    except mysql.connector.IntegrityError:
        return jsonify({'status': 'error', 'message': 'Username already used.'}), 400
    
    

@app.route('/game/<username>')
def game(username):
    try:
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Questions")
        questions_data = cursor.fetchall()
        questions = [{"id": data[0], "question": data[1], "choices": data[2].split(','), "answer": data[3]} for data in questions_data]
        conn.close()

        
        global isHost, Host, game_ongoing
        if game_ongoing:
            leave(username)
            return redirect('/')

        if Host:
            isHost = 0
        else:
            Host = username
            socketio.emit('update_lobby', 'Join')  
            isHost = 1
        
        return render_template('index.html', username = username, questions = questions, host = Host)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@socketio.on('lobby_started')
def lobby_started():
    socketio.emit("lobby_created")


@app.route('/start')
def start():
    global game_ongoing
    game_ongoing = True
    socketio.emit("start_game") 
    start_timer()

@socketio.on('connect')
def handle_connect():
    global game_ongoing
    if not game_ongoing:
        username = request.args.get('username')
        socketio.emit("player_joined", username)

@socketio.on('disconnect')
def handle_disconnect():
    print("Client Disconnected")
        


@socketio.on('request_highest_scores')
def handle_highest_scores():
    try:
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor()
        cursor.execute("SELECT username, score FROM Scores ORDER BY score DESC LIMIT 6") 
        scores = cursor.fetchall()
        conn.close()
        socketio.emit('update_highest_scores', {'status': 'success', 'scores': scores})
    except Exception as e:
        socketio.emit('update_highest_scores', {'status': 'error', 'message': str(e)})
        

def start_timer():
    global time_preferred
    start_time = time_preferred 

    while start_time > 0:
        start_time -= 1
        # Emit the current time to all connected clients
        socketio.emit('get_time', start_time)
        time.sleep(1)  # Wait for 1 second before updating the timer
        if game_ongoing == False:
            start_time = time_preferred
            return
    # When the countdown ends, emit a "quiz end" event
    socketio.emit('quiz_end')



@app.route('/leave', methods=['POST'])
def attempt_leave():
    username = request.form['username']
    leave(username)
    return "Left"


   
def leave(username):
    try:
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor()
        
        # DELETE users from the database
        cursor.execute("DELETE FROM scores WHERE username = %s", (username,))
        conn.commit() 

        global Host
        if Host == username:
            socketio.emit('host_left')

        return redirect('/')
    except Exception as e:
        return str(e)
    

@app.route('/delete')
def reset():
    try:
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor()
        
        # DELETE users from the database
        cursor.execute("DELETE FROM scores")
        conn.commit() 

        socketio.emit('update_lobby','Create')
        return redirect("/")
    except Exception as e:
        print(e)

@app.route('/check_answer', methods=['POST'])
def check_answer():
    try:
        data = request.json
        chosen_answer = data['chosen_answer']
        question_id = data['question_id']
        username = data['username']
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor()
        
        # Retrieve correct answer from the database
        cursor.execute("SELECT * FROM questions WHERE id = %s AND answer = %s", (question_id, chosen_answer))
        correct_answer = cursor.fetchone()
        conn.commit()
        # Compare chosen answer with correct answer
        if correct_answer is not None:
            try:
                # Add points because the answer is correct
                cursor.execute("UPDATE Scores SET score = score + 1 WHERE username = %s", (username,))
                conn.commit()
                print("This user: " + username) 
                conn.close()
                
                return jsonify({'status': 'correct'}), 200
            except Exception as e:
                print(e)
        else:
            return jsonify({'status': 'incorrect'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    

@app.route('/leaderboard')
def leaderboard():
    try:
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor()
        cursor.execute("SELECT username, score FROM Scores ORDER BY score DESC LIMIT 5") 
        scores = cursor.fetchall()
        conn.close()

        return render_template('leaderboards.html', users = scores)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    socketio.run(app)