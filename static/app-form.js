document.addEventListener("DOMContentLoaded", function(event){

    const loadingPage = function(e){
        const form = document.querySelector('#new_story_form')
        form.style.display = 'none';

        const loadingGif = document.querySelector('#loading')
        loadingGif.style.display = 'block';
    }

    const new_form = document.querySelector('#new_story_form')
    new_form.addEventListener('submit',loadingPage)

})

// revisit and create setTimeout function to disable when ChatGPT does not respond