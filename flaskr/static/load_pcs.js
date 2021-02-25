$(document).ready(function(){
    var user_size = 943
    var curr_user = 0
    var processes = 'TBD', chunksize = 'TBD';
    var progId = "#user-progress"

    $(progId).progress({
        percent: 0
    });

    $(progId).progress({
        total: 943
    });


    const progress_bar = {
        delimiters: ['[[', ']]'],
        data(){
            return{
                curr_user: 0,
                user_size: 943,
                labelTemplate: 'Preprocessing user {0} out of {1}'
            }
        },
        computed:{
            loadingLabel:{
                get(){
                    return `Preprocessing user ${this.curr_user} out of ${this.user_size}`
                }
            }
        }
    }
    const progBar = Vue.createApp(progress_bar).mount('#user-progress-label')

    var facts = [
            {fact: 'Unlike the Euclidean Distance similarity score (which is scaled from 0 to 1),\
                this metric measures how highly correlated are two variables and is measured from -1 to +1'},
            {fact: 'The Pearson Correlation score quantifies how well two data objects fit a line'},
            {fact: 'The accuracy of the score increases when data is not normalized.'},
            {fact: 'The Pearson Correlation score can correct for any\
                scaling within an attribute, while the final score is still being tabulated.'},
            {fact: 'Thus, objects that describe the same data but use different values can still be used.'},
            {fact: 'In essence, the Pearson Correlation score finds the ratio between the covariance and the standard deviation of both objects.'}

    ]

    var index = 0
    const fact_info = {
        delimiters: ['[[', ']]'],
        data() {
            return {
                curr_fact_index: index,
                fun_facts: facts
            }
        },
        computed: {
            curr_fact: {
                get() {
                    return this.fun_facts[this.curr_fact_index];
                    
                },
                set(newValue) {
                    this.fun_facts[this.curr_fact_index] = newValue;
                }
            }
        }
    }

    var info_facts = Vue.createApp(fact_info).mount('#info-fact')
    var index_image = -1
    const image_info = {
        delimiters: ['[[', ']]'],
        data () {
            return {
                image_index: index_image,
                'hidden content': false,
                'visible content': true,
                images : [
                    {url: '../static/pics/Euclidean_vs_Pearson.png', class:'visible content', image_index: 0},
                    {url: '../static/pics/geometric_interpretation.png', class:'hidden content', image_index: 1},
                    {url: '../static/pics/classification_accuracy.png', class:'hidden content', image_index: 2},
                    {url: '../static/pics/variations_of_function_similarity.png', class:'hidden content', image_index: 3},
                    {url: '../static/pics/PCS_examples.png', class: 'hidden content', image_index: 4},
                    {url: '../static/pics/PCS_formula.jpg', class: 'hidden content', image_index: 5}

                ]
            }
        },
        computed: {
            classObject() {
                index_image += 1
                return {
                    'hidden content' : index_image != 0,
                    'visible content': index_image == 0
                }
            }
        }
    }

    const app = Vue.createApp(image_info)

    app.component('image-item',{
        props: ['image'],
        template: `
        <div>
            <img :src="image.url" style="width: 100%;"/>
        </div>
        `
    });
    const info_images = app.mount('#info-images')
    
    process_info = {
        delimiters: ['[[', ']]'],
        data () {
            return {
                processes: processes,
            }
        }
        
    }
    
    const process_label = Vue.createApp(process_info).mount('#processLabel');
    
    const chunksize_label = Vue.createApp({
        delimiters: ['[[', ']]'],
        data () {
            return {
                chunksize: chunksize
            }
        }
    }).mount('#chunksizeLabel')

    var slide_map = {
        info_images: ''
    }

    $('.slickImage').slick({
        adaptiveHeight: true,
        autoplay:true,
        dots: true,
        autoplaySpeed: 7000,
        fade: true,
        arrows: true
    });
    console.log($('.slickImage').slick('slickCurrentSlide'));



    $('.slickImage').on('beforeChange', function(event, slick, currentSlide, nextSlide){
      //var index = currentSlide.currentSlide;
      info_facts.curr_fact_index = nextSlide;
      console.log(`Current user ${progBar.curr_user}`);
      console.log(`Current slide index = ${currentSlide}. Next slide index = ${nextSlide}`);
      //console.log(info_facts.curr_fact);
            //var index = $(currentSlide.$slides.get(cdrrentSlide)).data('caption');
      console.log(currentSlide);
      console.log(nextSlide);

    });

    console.log("Opening the SSE connection")
    var source = new EventSource("http://192.168.1.160:4503/recc/load_pcs_data")
    var stats_init = false
    console.log('Initialized Event Source for http://192.168.1.160:4503/recc/load_pcs_data')
    source.onerror =function(error){
        console.log(error)
    }

    source.onopen = function(){
        console.log("Connection opened...")
    }
    
    source.onmessage = function(event){
        event_data = event.data.replace(/&quot;/ig,"'");
        sent_data = JSON.parse(event_data);    
        console.log(sent_data);
        var done = false;
        if(!stats_init){
            processes = sent_data.processes;
            process_label.processes = sent_data.processes;
            chunksize = sent_data.chunksize;
            chunksize_label.chunksize = sent_data.chunksize;
            user_size = sent_data.total_size;
            stats_init = true;
        }
        percentage = Math.round((sent_data.records_affected / user_size) * 100);
        console.log(`Current Percentage: ${percentage} Records Affected: ${sent_data.records_affected}`);
        //Figure out why this increment stuff is buggin....lol get it
        $(progId).progress('increment');
        console.log($(progId).progress('get percent'));
        $(progId).progress('set percent', percentage);

        progBar.curr_user = sent_data.records_affected;
        if(sent_data.records_affected == user_size){
            console.log("Closing the SSE connection");
            
            source.close();

            window.location.assign("/recc/load_modern_data");
    
        }
    }

});









