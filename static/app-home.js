document.addEventListener("DOMContentLoaded", function(event){

    function reloadTable(stories){
        const tbody_stories = document.querySelector('#tbody_stories')

        while (tbody_stories.firstChild){
            tbody_stories.removeChild(tbody_stories.firstChild)
        }

        for(let i = 0; i<stories.length; i++){
            story = stories[i]
            console.log(story)

            const trow = document.createElement('tr')
            trow.setAttribute('class', 'table_rows')

            const td_title = document.createElement('td')
            td_title.setAttribute('class','story_titles')
            const title_anchor = document.createElement('a')
            title_anchor.setAttribute('href', `/story/${story.id}`)
            title_anchor.innerText = story.title 
            td_title.append(title_anchor)
            
            const base_lang = document.createElement('td')
            base_lang.innerText = story.base_language
            
            const foreign_lang = document.createElement('td')
            foreign_lang.innerText = story.foreign_language
            
            const sent_len = document.createElement('td')
            sent_len.innerText = story.sentences
            
            const total_tries = document.createElement('td')
            total_tries.innerText = story.attempts

            const high_score = document.createElement('td')
            high_score.innerText = `${story.max_score} %`

            const user_score = document.createElement('td')
            user_score.innerText = `${story.user_max_score} %`

            trow.append(td_title)
            trow.append(base_lang)
            trow.append(foreign_lang)
            trow.append(sent_len)
            trow.append(total_tries)
            trow.append(high_score)
            trow.append(user_score)

            tbody_stories.append(trow)

        }

    }

    const sortTableBy = async function (e){
        const base_lang = document.querySelector('#base_language_selection').value
        const foreign_lang = document.querySelector('#foreign_language_selection').value
        const already_sorted = e.target.getAttribute('data-asc', null)
        const sortBy = e.target.getAttribute('id')

        const response = await axios.get('/sort_table', {
            params:
            {base_lang : base_lang,
            foreign_lang : foreign_lang,
            already_sorted : already_sorted,
            sortBy : sortBy}})
        stories = response.data.stories
        evaluateAscendingDescending(e)
        reloadTable(stories)
    }

    const sortTableBySentenceLength = async function(e){
        const base_lang = document.querySelector('#base_language_selection').value
        const foreign_lang = document.querySelector('#foreign_language_selection').value
        const already_sorted = e.target.getAttribute('data-asc', null)
        
        const response = await axios.get('/orderby_sentence_count', {
            params:
            {base_lang:base_lang,
            foreign_lang: foreign_lang,
            already_sorted : already_sorted}})
        stories = response.data.stories
        evaluateAscendingDescending(e)
        reloadTable(stories)
    }

    const sortTableByAttempts = async function(e){
        const base_lang = document.querySelector('#base_language_selection').value
        const foreign_lang = document.querySelector('#foreign_language_selection').value
        const already_sorted = e.target.getAttribute('data-asc', null)
        const sortBy = e.target.getAttribute('id')

        const response = await axios.get('/orderby_attempts', {
            params:
            {base_lang : base_lang,
            foreign_lang : foreign_lang,
            already_sorted : already_sorted,
            sortBy : sortBy}})
        stories = response.data.stories
        evaluateAscendingDescending(e)
        reloadTable(stories)
        
    }

    const sortTableByHighestAllScores = async function(e){
        const base_lang = document.querySelector('#base_language_selection').value
        const foreign_lang = document.querySelector('#foreign_language_selection').value
        const already_sorted = e.target.getAttribute('data-asc', null)
        const sortBy = e.target.getAttribute('id')

        const response = await axios.get('/orderby_highest_score', {
            params:
            {base_lang : base_lang,
            foreign_lang : foreign_lang,
            already_sorted : already_sorted,
            sortBy : sortBy}})
        stories = response.data.stories
        evaluateAscendingDescending(e)
        reloadTable(stories)

    }

    const sortTableBYYourScore = async function(e){
        const base_lang = document.querySelector('#base_language_selection').value
        const foreign_lang = document.querySelector('#foreign_language_selection').value
        const already_sorted = e.target.getAttribute('data-asc', null)
        const sortBy = e.target.getAttribute('id')

        const response = await axios.get('/orderby_user_score', {
            params:
            {base_lang : base_lang,
            foreign_lang : foreign_lang,
            already_sorted : already_sorted,
            sortBy : sortBy}})
        stories = response.data.stories
        evaluateAscendingDescending(e)
        reloadTable(stories)

    }

    function evaluateAscendingDescending(e){
        const sorted = e.target.getAttribute('data-asc')
        if(sorted === null){
            addAscendingTrue(e.target)
        }
        else{
            removeAscending(e.target)
        }        
    }

    function addAscendingTrue(header){
        header.setAttribute('data-asc','true')
    }

    function removeAscending(header){
        header.removeAttribute('data-asc')
    }

    const filterTablebyLanguage = async function (e){
        const base_lang = document.querySelector('#base_language_selection').value
        const foreign_lang = document.querySelector('#foreign_language_selection').value

        if(base_lang === 'all' && foreign_lang === 'all'){
            const response = await axios.get('/load_table_all')
            const stories = response.data.stories
            reloadTable(stories)
        } 
        else{
            const response = await axios.get('/filter_by_language', {params: 
                {base_lang:base_lang,
                foreign_lang: foreign_lang}})
                stories = response.data.stories
            reloadTable(stories)
        }
    }

    const base_lang_filter = document.querySelector('#base_language_selection')
    base_lang_filter.addEventListener('change', filterTablebyLanguage)

    const foreign_lang_filter = document.querySelector('#foreign_language_selection')
    foreign_lang_filter.addEventListener('change', filterTablebyLanguage)

    const title_sort = document.querySelector('#title')
    title_sort.addEventListener('click', sortTableBy)

    const base_lang_sorting = document.querySelector('#base_language')
    base_lang_sorting.addEventListener('click',sortTableBy)

    const foreign_lang_sorting = document.querySelector('#foreign_language')
    foreign_lang_sorting.addEventListener('click', sortTableBy)

    const sentence_length_sort = document.querySelector('#sentences_length')
    sentence_length_sort.addEventListener('click', sortTableBySentenceLength)

    const total_attempts_sort = document.querySelector('#total_attempts')
    total_attempts_sort.addEventListener('click', sortTableByAttempts)

    const all_high_scores = document.querySelector('#all_high_score')
    all_high_scores.addEventListener('click', sortTableByHighestAllScores)

    const your_high_scores = document.querySelector('#your_high_score')
    your_high_scores.addEventListener('click', sortTableBYYourScore)



})