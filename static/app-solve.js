document.addEventListener("DOMContentLoaded", function(event){

  // Loads the blocks of sentences after the Begin-Button is selected.
  const clickLoadSentenceTest = async function(e){
    e.target.style.display = "none"
      
      const score_tracker = document.createElement('span')
      const div_score_display = document.createElement('div')
      div_score_display.setAttribute('id','div_score_display')
      const score_word = document.createElement('span')
      score_word.innerText = 'Correct Guesses / Total Guesses: '
      const out_of_score = document.createElement('span')
      out_of_score.setAttribute('id','total_story_points')
      const story_top = document.querySelector("#story_top")

      score_tracker.setAttribute('id','score')

      div_score_display.append(score_word)
      div_score_display.append(out_of_score)
      div_score_display.append(score_tracker)      
      story_top.append(div_score_display)

      const response = await axios.get('/load_sentences')
      sentences = response.data.sentences_list
      score_tracker.innerText = response.data.total_points      
      out_of_score.innerText = `${response.data.total_points} / `

      for(let i = 0; i < sentences.length; i++){
        createSentenceBlocks(sentences[i], i)
    }
  }

  // Add event listener to begin-beginButton.
  const beginButton = document.querySelector("#begin_button");
  beginButton.addEventListener("click", clickLoadSentenceTest)

  const playAudio = async function generateAndPlayAudio(e){
    const sentenceId = e.target.getAttribute('data-sentence')
    try {
      const response = await axios.post('/play_sentence', {
          sentence_id : sentenceId
      });

      // Assuming the server responds with a link to the generated audio file
      const audioUrl = response.data.audio_url;

      // Create an audio element and play the audio
      const audio = new Audio(audioUrl);
      audio.play();
    } catch (error) {
      console.error('Error:', error);
    }
  }

  const wordTest = async function checkWordSelection (e){
    word_span = e.target
    const response = await axios.post('/check_correctness',{guess: word_span.innerText, sentence: word_span.getAttribute('data-block')})
    sentence_end = response.data.sentence_end
    next_sentence_id = response.data.next_sentence_id
    word_correct = response.data.word_correct
    word_id = response.data.word_id
    word_text = response.data.word_text  
    points = response.data.points  
    total_points = response.data.total_points

    if(word_correct){
      const wrong_ans = document.querySelectorAll('span.red')
      for (const ans of wrong_ans){
        ans.classList.remove('red')
      }

      sent_num = word_span.getAttribute('data-block')
      word_span.setAttribute('class', 'option green')
      word_span.removeEventListener('click', wordTest)
      const new_word = document.createElement('span')
      new_word.setAttribute('class', 'answer')
      new_word.innerText = word_text
      const block = document.querySelector(`.block${sent_num}`)
      const blockAnswer = block.querySelector('.test_answer')
      blockAnswer.append(new_word)
    }

    if(sentence_end){
      const play_audio = document.createElement('span')
      play_audio.addEventListener('click', playAudio)
      play_audio.innerText ='Play Sentence';
      play_audio.setAttribute('data-sentence',next_sentence_id - 1)
      play_audio.classList.add('play_button')
      const last_block = document.querySelector(`.block${sent_num}`)
      const last_blockAnswer = last_block.querySelector('.test_answer')
      last_blockAnswer.append(play_audio)
    }

    if(sentence_end && next_sentence_id){
      const new_block = document.querySelector(`.block${next_sentence_id}`)
      new_block.classList.remove('class','hidden')
    }

    if(word_correct === false){
      word_span.classList.add('red')
    }

    updateScore(points, total_points)

    if(next_sentence_id === false){
      const score = await saveScore()
      endStoryGame(score)
    }
  }

  function endStoryGame(score){
    const banner = document.createElement('div')
    banner.setAttribute('id', 'finished_banner')
    banner.innerText = `Your final score is ${score}%!`

    const story_top = document.querySelector('#story_top')
    const div_score_display = document.querySelector('#div_score_display')
    div_score_display.setAttribute('class', 'hidden')
    story_top.append(banner)

    const button_div = document.createElement('div')
    const try_again_button = document.createElement('button')
    const home_button = document.createElement('button')

    const try_again_a = document.createElement('a')
    const home_a = document.createElement('a')

    const story_id = document.querySelector('#story_title')
    const id = story_id.getAttribute('data-id')
    
    try_again_a.setAttribute('href',`/story/${id}`)
    home_a.setAttribute('href','/')

    try_again_a.innerText = 'Play Story Again'
    home_a.innerText = 'Return Home'
    
    story_top.append(button_div)
    button_div.append(try_again_button)
    button_div.append(home_button)
    try_again_button.append(try_again_a)
    home_button.append(home_a)


  }
  
  async function saveScore(){
    response = await axios.post('/save_score')
    return response.data.score
  }

  function updateScore(points, total_points){
    const total_story_points = document.querySelector('#total_story_points')
    total_story_points.innerText = `${total_points} / `   

    const score = document.querySelector('#score')
    score.innerText = points
  }

  function createSentenceBlocks(sentence_test, i){
    const test_block = document.createElement('div')
    const test_sentence = document.createElement('div')
    const test_answer = document.createElement('div')
    const test_options = document.createElement('div')
    const story_container = document.querySelector('#story_container')

    test_block.setAttribute('class', `block${i}`)
    test_block.classList.add('test_block')
    test_block.setAttribute('data-block', i)    
    test_sentence.innerText = sentence_test['base_sentence']
    test_sentence.setAttribute('class','test_sentence')
    test_answer.setAttribute('class','test_answer')
    test_answer.innerText = 'Build Answer Here:'    
    test_options.setAttribute('class', 'test_options')

    if(i!==0){
      test_block.classList.add('class', 'hidden')
    }

    for(words of sentence_test['random_translated_sentence_list']){
      const word = document.createElement('span')
      word.innerText = words
      word.setAttribute('data-block',i)
      word.setAttribute('class','option')

      word.addEventListener('click', wordTest)

      test_options.append(word)      
    }

    test_block.append(test_sentence)
    test_block.append(test_answer)
    test_block.append(test_options)
    
    story_container.append(test_block)
  }





})
