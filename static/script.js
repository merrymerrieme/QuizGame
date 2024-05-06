let count = 0, TIMER = 100, ongoing = false
const socket = io({query : {username : USERNAME}});


$("#start").click(function(){
    ongoing = true
    $.ajax({
        url: "/start"
    })
})

$("#leave").click(function(){
   leave()
})

function leave(){
    $.ajax({
        url: "/leave",
        type: "POST",
        data: {
            username : USERNAME
        },success:function(){
            requestHighestScores()
            location.replace("/")
        }
    })
}

socket.on("start_game", function(){
    document.getElementById("start").style.display = "none";
            // Check if there are questions available
            if (QUESTIONS.length > 0) {
                startQuiz(USERNAME, QUESTIONS);
            } else {
                alert("No questions available.");
            }
})


socket.on('connect', function(data){
    socket.emit("lobby_started")
})



socket.on("player_joined", function(data){
    if(data && data !== "undefined") {
        player_alert = `${data} has joined!`;

        Swal.fire({
            position: "center",
            icon: "info",
            title: player_alert,
            showConfirmButton: false,
            timer: 1000
        });
    }
})

socket.on('lobby_created', function(data){
    if(HOST != USERNAME){
        $('#start').hide()
    }
})

socket.on('display_question', function(data) {
    count = data.question_number;
    displayQuestion(question[count])
    // Display the question corresponding to the question number
});

socket.on('get_time', function(data){
    let counter = document.getElementById("timer")
    counter.innerHTML = data
})

socket.on('update_highest_scores', function(data) {
    if (data.status === 'success') {
        // Update leaderboard with the latest scores
        console.log(data.scores)
        updateLeaderboard(data.scores);
    } else {
        console.error('Error:', data.message);
    }
});



socket.on('quiz_end', function(data){
    window.location.href = "/leaderboard"
})

socket.on('host_left', function(data){
    window.location.href = '/delete'
})

function requestHighestScores() {
    socket.emit('request_highest_scores');
}


requestHighestScores()


function startQuiz(username, questions) {
// Display the first question and start the quiz process
count = Math.round((Math.random() * 10000) % 50)
displayQuestion(questions[count]);
}

function displayQuestion(question) {
document.getElementById('quiz-area').innerHTML = `
    <h4 id= "question">${question.question}</h4>
    <div id="choices">
        ${question.choices.map((choice, index) => `
            <button class="button" onclick="checkAnswer('${choice}', ${question.id})">${choice}</button>
        `).join('')}
    </div>
`;
}



function checkAnswer(choice, questionId) {
    const chosenAnswer = choice;
    const qId = questionId;

    const requestBody = JSON.stringify({
    chosen_answer: chosenAnswer,
    question_id: qId,
    username: USERNAME
    });

    fetch('/check_answer', {
    method: 'POST',
    headers: {
    'Content-Type': 'application/json'
    },
    body: requestBody
    })
    .then(response => {
    if (!response.ok) {
    throw new Error('Network response was not ok');
    }
    return response.json();
    })
    .then(data => {
    if (!data.status) {
    alert("There was an error processing your answer");
    return;
    }
    if (data.status === 'correct') {
        Swal.fire({
            position: "center",
            icon: "success",
            title: "Correct!",
            showConfirmButton: false,
            timer: 600
        });
    } else {
        Swal.fire({
            position: "center",
            icon: "error",
            title: "Incorrect!",
            showConfirmButton: false,
            timer: 600
        });
    }
    // Display the next question or handle quiz completion as needed

    requestHighestScores()
    count = Math.round((Math.random() * 10000) % 50)
    displayQuestion(QUESTIONS[count]);
    })
    .catch(error => {
    console.error('Error:', error);
    alert("There was an error processing your answer");
    });
    }

    function updateLeaderboard(scores) {
    const leaderboard = document.getElementById('lboard');
    leaderboard.innerHTML = '';

    scores.forEach(score => {
    const listItem = document.createElement('li');
    listItem.textContent = `${score[0]} - ${score[1]}`;
    leaderboard.appendChild(listItem);
    });


}

