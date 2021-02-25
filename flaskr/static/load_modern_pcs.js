$(document).ready(function(){
    var contentVue,extraContentVue, imageVue, ratingsVue, processVue, chunksizeVue, progBarVue;
    var yt_players = new Map();
    //TODO: Change this later to api call, maybe
    var movie_rating = 3;
    var temp_image = 'https://cdn.hipwallpaper.com/m/45/15/tjBl12.jpg';
    var signedIn = false;
    var loginAlert = false;
    var process_num = 'TBD';
    var chunksize_num = 'TBD';
    var progId = "#user-progress";
    var ytApiReady = false;


    var email, password;
    //TODO: Create the "still there?" message lol, maybe
    $(progId).progress({
        percent: 0
    });

    $(progId).progress({
        total: 610
    });


    var dimmerFunc = {
        on: 'hover',
        onShow: function(){
            var id = $(this).attr('id');
            //console.log(`YT OnMouseEnter for id ${id}`);
            var player = yt_players.get(id);
            console.log(`Player type: ${typeof(player)}`);
            console.log(player);
            if( typeof(player) !== 'undefined' && player.getPlayerState() == YT.PlayerState.PAUSED){
                console.log(`About to resume video`);
                player.playVideo();
            }
        },
        onHide: function(){
            var id = $(this).attr('id');
            //console.log(`YT OnMouseEnter for id ${id}`);
            var player = yt_players.get(id);
            console.log(`Player type: ${typeof(player)}`);
            console.log(player);
            if( typeof(player) !== 'undefined' && player.getPlayerState() == YT.PlayerState.PLAYING){
                console.log(`About to pause video`);
                player.pauseVideo();
            }
        },
    }
    
    
    $('.special.cards .image').dimmer(dimmerFunc);
    //Change where you put this later on
    function createContentVue(mountPoint){
        //TODO: Change id to be zero indexed
        contentVue = Vue.createApp({
            delimiters: ['[[', ']]'],
            data () {
                return {
                    movie_index: 0,
                    movies: [
                        {'id': 1, 'title': 'Thor Ragnarok', 'synopsis': 'Imprisoned on the planet Sakaar, Thor must race against time to return to Asgard and stop Ragnarök, the destruction of his world, at the hands of the powerful and ruthless villain Hela.', 'rating': 'PG-13', 'genres':'Action, Adventure, Comedy', 'release_date': 'November 3, 2017 (USA)'},
                        {'id': 2, 'title': '42', 'synopsis': 'In 1947, Jackie Robinson becomes the first African-American to play in Major League Baseball in the modern era when he was signed by the Brooklyn Dodgers and faces considerable racism in the process.', 'rating': 'PG-13', 'genres':'Biography, Drama, Sport','release_date': 'April 12, 2013 (USA)'},
                        {'id': 3, 'title': 'Bridesmaids', 'synopsis': "Competition between the maid of honor and a bridesmaid, over who is the bride's best friend, threatens to upend the life of an out-of-work pastry chef.", 'rating': 'R', 'genres':'Comedy, Romance','release_date': 'May 13, 2011 (USA)'},
                        {'id': 4, 'title': 'Django Unchained', 'synopsis': "Two years before the Civil War, Django (Jamie Foxx), a slave, finds himself accompanying an unorthodox German bounty hunter named Dr. King Schultz (Christoph Waltz) on a mission to capture the vicious Brittle brothers. Their mission successful, Schultz frees Django, and together they hunt the South's most-wanted criminals. Their travels take them to the infamous plantation of shady Calvin Candie (Leonardo DiCaprio), where Django's long-lost wife (Kerry Washington) is still a slave.", "rating": 'R', "genres":"Drama, Western","release_date": "25 December 2012 (USA)"},
                        {'id': 5, 'title': 'The Lion King 1½', 'synopsis': "From their uniquely hysterical perspective, Timon and his windy pal Pumbaa - the greatest unsung heroes of the Savanna - reveal where they came from, how they helped Simba save the Serengeti, and what really happened behind the scenes of The Lion King's biggest events.", "rating": 'G', "genres":"Adventure, Animation, Children, Comedy","release_date": "February 9, 2004 (USA)"},
                        {'id': 6, 'title': 'Zero Dark Thirty', 'synopsis': "Following the terrorist attacks of Sept. 11, 2001, Osama bin Laden becomes one of the most-wanted men on the planet. The worldwide manhunt for the terrorist leader occupies the resources and attention of two U.S. presidential administrations. Ultimately, it is the work of a dedicated female operative (Jessica Chastain) that proves instrumental in finally locating bin Laden. In May 2011, Navy SEALs launch a nighttime strike, killing bin Laden in his compound in Abbottabad, Pakistan.", "rating": 'R', "genres":"Drama, History, Thriller","release_date": "January 11 2013 (USA)"},
                      {'id': 7, 'title': 'The Truman Show', 'synopsis': "He doesn't know it, but everything in Truman Burbank's (Jim Carrey) life is part of a massive TV set. Executive producer Christof (Ed Harris) orchestrates 'The Truman Show' a live broadcast of Truman's every move captured by hidden cameras. Cristof tries to control Truman's mind, even removing his true love, Sylvia (Natascha McElhone), from the show and replacing her with Meryl (Laura Linney). As Truman gradually discovers the truth, however, he must decide whether to act on it.", "rating": 'PG', "genres":" Comedy, Drama","release_date": "June 5 1998 (USA)"},
                      {'id': 8, 'title': 'The Pursuit of Happyness', 'synopsis': "Life is a struggle for single father Chris Gardner (Will Smith). Evicted from their apartment, he and his young son (Jaden Christopher Syre Smith) find themselves alone with no place to go. Even though Chris eventually lands a job as an intern at a prestigious brokerage firm, the position pays no money. The pair must live in shelters and endure many hardships, but Chris refuses to give in to despair as he struggles to create a better life for himself and his son.", "rating": 'PG-13', "genres":"Biography, Drama","release_date": "December 15 2006 (USA)"},
                      {'id': 9, 'title': 'Sausage Party', 'synopsis': "Life is good for all the food items that occupy the shelves at the local supermarket. Frank (Seth Rogen) the sausage, Brenda (Kristen Wiig) the hot dog bun, Teresa Taco and Sammy Bagel Jr. (Edward Norton) can't wait to go home with a happy customer. Soon, their world comes crashing down as poor Frank learns the horrifying truth that he will eventually become a meal. After warning his pals about their similar fate, the panicked perishables devise a plan to escape from their human enemies.", "rating": 'R', "genres":"Animation, Adventure, Comedy","release_date": "August 12 2016 (USA)"},
                      {'id': 10, 'title': 'The Social Network', 'synopsis': "Deena, Effie and Lorrell form a music trio called the Dreamettes. When ambitious manager Curtis Taylor Jr. spots the act at a talent show, he offers the chance of a lifetime, to be backup singers for a national star. Taylor takes creative control of the group and eventually pushes the singers into the spotlight. However, one becomes the star, forcing another out, which teaches them about the high cost of fame.", "rating": 'PG-13', "genres":"Biography, Drama ","release_date": "October 1 2010 (USA)"}
                    ], 
                }
            },
            computed: {
                curr_movie: {
                    get() {
                        return this.movies[this.movie_index];
                    },
                    set(newValue){
                        this.movies[this.movie_index] = newValue;
                    }
                    
                }
            }
        }).mount(mountPoint);
    }
    //TODO: Code for added directors
    function createExtraContentVue(mountPoint){
        extraContentVue = Vue.createApp({
            delimiters: ['[[', ']]'],
            data () {
                return {
                    movie_index: 0,
                    movies: [
                        {'id': 1, 'director': 'Taika Waititi', 'stars': 'Chris Hemsworth, Tom Hiddleston, Cate Blanchett','writers': 'Eric Pearson, Craig Kyle', 'imageUrl':'https://wallpapercave.com/wp/wp2497187.jpg',"imdb":"7.9/10","rottenTomatoes":"93%", "metacritic":"74%", 'trailerCode': 'ue80QwXMRHg'},
                        {'id': 2, 'director': ' Brian Helgeland', 'stars': 'Chadwick Boseman, T.R. Knight, Harrison Ford', 'writers': 'Brian Helgeland', 'imageUrl':'https://wallpapercave.com/wp/wp3028527.png', "imdb": "7.5/10", "rottenTomatoes":"81%", "metacritic":"62%", 'trailerCode': 'I9RHqdZDCF0'},
                        {'id': 3, 'director': 'Paul Feig', 'stars': 'Kristen Wiig, Maya Rudolph, Rose Byrne', 'writers': 'Kristen Wiig, Annie Mumolo', 'imageUrl':'https://images5.alphacoders.com/398/398206.png', "imdb":"6.8/10", "rottenTomatoes":"90%", "metacritic":"75%", 'trailerCode': 'PP9l4LP0WPI'},
                        {'id': 4, 'director': 'Quentin Tarantino', 'stars': 'Jamie Foxx, Christoph Waltz, Leonardo DiCaprio','writers':'Kristen Wiig, Annie Mumolo', 'imageUrl':'https://wallpapercave.com/wp/wp2100208.jpg', "imdb":"8.4/10", "rottenTomatoes":"87%", "metacritic":"81%", 'trailerCode': '0fUCuvNlOCg'},
                        {'id': 5, 'director': 'Bradley Raymond', 'stars': 'Nathan Lane, Ernie Sabella, Matthew Broderick','writers': 'Tom Rogers', 'imageUrl':'https://wallpapercave.com/wp/wp1849327.jpg', "imdb": "6.5/10", "rottenTomatoes": "78%", "metacritic":"NA", 'trailerCode': 'p0DTnqn71WQ'},
                        {'id': 6, 'director': 'Kathryn Bigelow', 'stars': 'Jessica Chastain, Joel Edgerton, Chris Pratt', 'writers': 'Mark Boal', 'imageUrl':'https://images5.alphacoders.com/369/369997.jpg',"imdb": "7.4/10", "rottenTomatoes": "91%", "metacritic":"95%", 'trailerCode': 'LJFra3B9sbA'},
                        {'id': 7, 'director': 'Peter Weir', 'stars': 'Jim Carrey, Ed Harris, Laura Linney', 'writers': 'Andrew Niccol', 'imageUrl':'https://images2.alphacoders.com/694/694037.jpg', "imdb": "8.1/10", "rottenTomatoes": "95%", "metacritic": "90%", 'trailerCode': 'dlnmQbPGuls'},
                        {'id': 8, 'director': 'Gabriele Muccino', 'stars': "Will Smith, Thandie Newton, Jaden Smith", 'writers': "Steve Conrad (as Steven Conrad)", 'imageUrl':'https://qph.fs.quoracdn.net/main-qimg-a227e517927f68ce7e40b1de65fa4254-c', "imdb": "8/10", "rottenTomatoes": "67%", "metacritic": "64%", 'trailerCode': 'DMOBlEcRuw8'},
                        {'id': 9, 'director': 'Greg Tiernan, Conrad Vernon', 'stars': 'Seth Rogen, Kristen Wiig, Jonah Hill', 'writers': 'Kyle Hunter, Ariel Shaffir', 'imageUrl':'https://wallpapercave.com/wp/wp2455712.jpg', "imdb": "6.1/10", "rottenTomatoes": "82%", "metacritic": "66%", 'trailerCode': 'WVAcTZKTgmc'},
                      {'id': 10, 'director': 'David Fincher', 'stars': 'Jesse Eisenberg, Andrew Garfield, Justin Timberlake', 'writers': 'Aaron Sorkin, Ben Mezrich', 'trailerCode': 'dlnmQbPGuls'}
                    ], 
                }
            },
            computed: {
                curr_movie: {
                    get() {
                        return this.movies[this.movie_index];
                    },
                    set(newValue){
                        this.movies[this.movie_index] = newValue;
                    }
                    
                }
            }
        }).mount(mountPoint);
    }
    
    function createImageVue(mountPoint){
        const app = Vue.createApp({
            delimiters: ['[[', ']]'],
            data () {
                return {
                    images: [
                        {'dimmer_id': 'dimmer_1','title_id': 'title_1', 'image_id': 'image_1', 'url': 'https://wallpapercave.com/wp/wp2497190.jpg'},
                        {'dimmer_id': 'dimmer_2','title_id': 'title_2', 'image_id': 'image_2', 'url': 'https://wallpapercave.com/wp/wp3028527.png'},
                        {'dimmer_id': 'dimmer_3','title_id': 'title_3', 'image_id': 'image_3', 'url': 'https://wallpapercave.com/wp/wp5268557.jpg'},
                        {'dimmer_id': 'dimmer_4','title_id': 'title_4', 'image_id': 'image_4', 'url': 'https://wallpapercave.com/wp/wp2100208.jpg'},
                        {'dimmer_id': 'dimmer_5','title_id': 'title_5', 'image_id': 'image_5', 'url': 'https://wallpapercave.com/wp/wp1849327.jpg'},
                        {'dimmer_id': 'dimmer_6','title_id': 'title_6', 'image_id': 'image_6', 'url': 'https://images5.alphacoders.com/369/369997.jpg'},
                        {'dimmer_id': 'dimmer_7','title_id': 'title_7', 'image_id': 'image_7', 'url': 'https://images2.alphacoders.com/694/694037.jpg'},
                        {'dimmer_id': "dimmer_8","title_id": "title_8", "image_id": "image_8", "url": "https://qph.fs.quoracdn.net/main-qimg-a227e517927f68ce7e40b1de65fa4254-c"},
                      {'dimmer_id': "dimmer_9","title_id": "title_9", "image_id": "image_9", "url": "https://wallpapercave.com/wp/wp2455712.jpg"},
                      {'dimmer_id': "dimmer_10","title_id": "title_10", "image_id": "image_10", "url": "https://wallpapercave.com/wp/wp2126142.jpg"}
                   ]
                }
            }
        });
      
        app.component('image-item',{
            props: ['image'],
            template: `
                    <div>
                        <div v-bind:id="image.dimmer_id" class="blurring dimmable image">
                            <div class="ui dimmer">
                                <div class="content">
                                    <div class="center">
                                        <div v-bind:id="image.title_id" class="player_button">
                                            <button class="huge massive circular ui icon inverted button">
                                                <i style="font-size: inherit;" class="play icon"></i>
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <img v-bind:id="image.image_id" :src="image.url" style="width: 100%;">
                       
                        </div>
                    </div>
            `
        });
        
        imageVue = app.mount(mountPoint);
        
    }
  
    
    function createRatingsVue(mountPoint){
        ratingsVue = Vue.createApp({
            delimiters: ['[[', ']]'],
            data () {
                return {
                    rating_index: 0,
                    ratings:[
                        {'id':1 ,'imdb': '7.9/10', 'rottenTomatoes':'93%', "metacritic":"74%"},
                        {'id':2 ,'imdb': '7.5/10', 'rottenTomatoes':'81%', "metacritic":"62%"},
                        {'id':3 ,'imdb': "6.8/10", 'rottenTomatoes':"90%", "metacritic":"75%"},
                        {'id':4 ,'imdb': "8.4/10", "rottenTomatoes":"87%", "metacritic":"81%"},
                        {'id':5 ,'imdb': "6.5/10", "rottenTomatoes":"78%", "metacritic":"Not Available"},
                        {'id':6 ,'imdb': "7.4/10", "rottenTomatoes":"91%", "metacritic":"95%"},
                        {'id':7 ,'imdb': "8.1/10", "rottenTomatoes":"95%", "metacritic":"90%"},
                        {'id':8 ,'imdb': "8/10", "rottenTomatoes":"67%", "metacritic":"64%"},
                        {'id':9 ,'imdb': "6.1/10", "rottenTomatoes":"82%", "metacritic":"66%"},
                        {'id':10 ,'imdb': "7.7/10", "rottenTomatoes":"96%", "metacritic":"95%"}

                    ]
                }
            },
            computed: {
                curr_rating: {
                    get() {
                        return this.ratings[this.rating_index];
                    },
                    set(newValue){
                        this.ratings[this.rating_index] = newValue;
                    }
                    
                }
            }
        }).mount(mountPoint);
    }

    function createMetadataVues(processMountPoint, chunksizeMountPoint){
        
        var process_info = {
            delimiters: ['[[', ']]'],
            data () {
                return {
                    processes: process_num,
                }
            }
            
        }
        
        processVue = Vue.createApp(process_info).mount(processMountPoint);
        
        chunksizeVue = Vue.createApp({
            delimiters: ['[[', ']]'],
            data () {
                return {
                    chunksize: chunksize_num,
                }
            }
        }).mount(chunksizeMountPoint);
    }

    function createProgBarVue(mountPoint){
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
        progBarVue = Vue.createApp(progress_bar).mount(mountPoint)
    }
       
    function setImageHeights(list, height){
        for(var i = 1; i < list.length; i++){
            var id = list[i]['id'];
            $(`#image_${id}`).css('height', height);
        }
    }
    window.onYouTubeIframeAPIReady = function (){
        console.log('YouTube API is ready');
    } 
    
    
    function playerButtonOnClick(curr_obj){

        var id = $(curr_obj).attr('id');
        var num_id = id.substring(id.length - 1);
        console.log(`Button id: ${id}, num_id: ${num_id}, image_${num_id}`);
        var width = $(`#image_${num_id}`).width();
        var height = $(`#image_${num_id}`).height();
        var player = new YT.Player(id, {
            height: height,
            width: width,
            videoId: extraContentVue.movies[parseInt(num_id) - 1].trailerCode,
            events: {
                'onReady': onPlayerReady,
                'onStateChange': onPlayerStateChange
            }
        });
    }

    $('#transition_button').click(function(){
        $('#intro_card').transition('scale');
        
        window.setTimeout(function(){
            $("#udacity_logo").transition('fade');
        }, 200);
        
        window.setTimeout(function(){

            $('#main_card').transition('scale');
            createContentVue('#card_content');
            createExtraContentVue('#extra_card_content');
            createImageVue('#info_images');
            createRatingsVue('#ratings_content');
            createMetadataVues('#processLabel', '#chunksizeLabel');
            createProgBarVue('#user-progress-label');

            $('.special.cards .image').dimmer(dimmerFunc);  
            $('.player_button').click(function(){ playerButtonOnClick(this); });
            $(".rating").rating({
                icon: 'star',
                initialRating: 3,
                maxRating: 5,
                onRate: function(value){
                    if(signedIn == false && loginAlert == false){
                        alert('Please login first.');
                        loginAlert = true;
                        //TODO: Change to default later
                        $(".rating").rating('set rating', 3);
                        return;
                    }
                    loginAlert = false;
                    
                }
                
            });
            $("#login_label").click(function(){
                $('.tiny.ui.modal').modal('show');
                $('#login_button').click(function(){
                    email = $("#email_input").val();
                    password = $("#password_input").val();
                    console.log(`User email: ${email}`);
                    console.log(`User password: ${password}`);
                    $("#login_label")
                    $('.tiny.ui.modal').modal('hide');
                    signedIn = true;
                    $('#login_label').transition('fade');
                    
                });
            });
            // Define function for setting height for all images programatically
            var height = $('#image_1').height();
            console.log(`Image 1 height ${height}`)
            console.log(contentVue);
            console.log(extraContentVue);
            setImageHeights(contentVue.movies, height);
            $('.slickImage').slick({
                autoplay:true,
                dots: false,
                autoplaySpeed: 7000,
                fade: true,
                arrows: true
            });
            $('.slickImage').slick('refresh');




        }, 1000);
        
        window.setTimeout(function(){
            $('#process_div').transition('fade down');  
        }, 1100);
        
        window.setTimeout(function(){
            $('#chunksize_div').transition('fade down');
        }, 1200);
        window.setTimeout(function(){
            $('#user-progress').transition('fade down');  
        }, 1300);
       
    });
    
    
    function onPlayerReady(event){
        var id = event.target.getIframe().id;
        var num_id = id.substring(id.length - 1);
        console.log('Playing video');
        console.log(event.target);
        event.target.playVideo();
        yt_players.set(`dimmer_${num_id}`, event.target);
    }
    
    function onPlayerStateChange(event){
        
      //TODO: Add on reset for videos that have filler at the end.
        if(event.data == YT.PlayerState.ENDED){
            var id = event.target.getIframe().id;
            console.log('Video Ended');
            console.log(id);
            var num_id = id.substring(id.length - 1);

            var tag = document.createElement('div');
            tag.className = "check_in";
            tag.innerHTML = "U Done?";

            var dimmerTag, contentTag, messageTag, yesTag, noTag;

            dimmerTag = document.createElement('div');
            dimmerTag.className = "ui dimmer";
            dimmerTag.id = `temp_${num_id}`;

            contentTag = document.createElement('div');
            contentTag.className = "content";

            messageTag = document.createElement('h2');
            messageTag.className = "ui inverted header";
            messageTag.id = `ending_header_${num_id}`;
            messageTag.innerHTML = 'U Done?';
            messageTag.style.fontWeight = '100';

            yesTag = document.createElement('button');
            yesTag.className = "circular ui inverted purple button reset";
            yesTag.id = `reset_${num_id}`;
            yesTag.style.width = '100px';
            yesTag.innerHTML = "Yes";
            yesTag.style.margin = "10px 50px 0px 0px";

            
            noTag = document.createElement('button');
            noTag.className = "circular ui inverted button";
            noTag.style.margin = "10px 0px 0px 50px";
            noTag.style.width = '100px';
            noTag.innerHTML = "Not Yet";

            var tags = [dimmerTag, contentTag, messageTag];        
            for(var i = 1; i < tags.length; i++){
              tags[i-1].appendChild(tags[i]);
            }


            $(yesTag).insertAfter(messageTag);
            $(noTag).insertAfter(yesTag);
            $(dimmerTag).insertBefore(`#title_${num_id}`);
            console.log(`Inserting Tag...`);
            console.log(dimmerTag);


            $(`#temp_${num_id}`).dimmer('show'); 
            
            $('.reset').click(function(){
                resetOnClick(this);
            });
        }
    }
    
    function resetOnClick(curr_obj){
        var id = $(curr_obj).attr('id');
        console.log(`User is done with video. Video Id ${id}`);
        var num_id = id.substring(id.length - 1);
        var buttonDiv = document.createElement('div');
        buttonDiv.className = "player_button";
        buttonDiv.id = `title_${num_id}`;

        var button = document.createElement('button');
        button.className = "huge massive circular ui icon inverted button";
        
        var icon = document.createElement('i');
        icon.className = "play icon";
        icon.style.fontSize = "inherit";

        buttonDiv.appendChild(button);
        
        button.appendChild(icon);

        $(`#temp_${num_id}`).dimmer('hide');
        $(`#title_${num_id}`).replaceWith(buttonDiv);
        $(`#temp_${num_id}`).detach();
        
        //TODO: Might find a better way of doing this
        $('.player_button').click(function(){playerButtonOnClick(this);});
        yt_players.delete(`#dimmer_${num_id}`);
        
    }
    
    
    $('.slickImage').on('beforeChange', function(event, slick, currentSlide, nextSlide){
        //console.log(`CurrentSlide : ${currentSlide}, NextSlide: ${nextSlide}`);
        //console.log(extraContentVue);
        contentVue.movie_index = nextSlide;
        extraContentVue.movie_index = nextSlide;
        ratingsVue.rating_index = nextSlide;
    });
    //$('#intro_card').transition('scale')

    console.log("Opening the SSE connection")
    var source = new EventSource("/recc/load_modern_pcs_data");
    var stats_init = false;
    var user_size, event_data, sent_data, percentage;


    console.log('Initialized Event Source for /recc/load_pcs_data');
    source.onerror =function(error){
        console.log(error);
    }
    
    source.onmessage = function(event){
        event_data = event.data.replace(/&quot;/ig,"'");
        sent_data = JSON.parse(event_data);    
        console.log(`Data recieved: ${sent_data}`);
        var done = false;
        if(!stats_init){
            process_num = sent_data.processes;
            processVue.processes= sent_data.processes;
            chunksize_num = sent_data.chunksize;
            chunksizeVue.chunksize = sent_data.chunksize;
            user_size = sent_data.total_size;
            stats_init = true;
            $.ajax({
                url: "/recc/get_credentials",
                type: "GET",
                success: function(result){
                    console.log(result);
                },
                error: function(error){
                    console.log(`Error ${error}`);
                }
            });
        }
        percentage = Math.round((sent_data.records_affected / user_size) * 100);
        console.log(`Current Percentage: ${percentage} Records Affected: ${sent_data.records_affected}`);
        //Figure out why this increment stuff is buggin....lol get it
        $(progId).progress('increment');
        console.log($(progId).progress('get percent'));
        $(progId).progress('set percent', percentage);

        progBarVue.curr_user = sent_data.records_affected
        if(sent_data.records_affected == user_size){
            console.log("Closing the SSE connection");
            source.close();
            window.location.assign("/");
    
        }
    }
});