# Movielens Reccomender
If anyone happens to 'stumble' across this repo, this README is just a collection of thoughts for my future self, if I ever choose to comeback to this project. 
## Note to Self

### Cloud Run/Kubernetes/Google Anthos
The initial goal of this iteration of the MovieLens Recommender was to make sense of Google Anthos. I don't think I fully accomplished that since I just had to look it up. The infamous search engine tells me it is a 'managed application platform that extends Google Cloud services and engineering practices to your environments'. 

Although I found out this was not possible to do for free(kind of) and not worth paying for, I decided to try and replicate the workplace enviroment(the trenches) and get some experience in deploying applications/devops work(not really, but I would like to think so).

This was also supposed to be a playground for a potential usecase for project HeyBigHead. 

From what I understand, Google Anthos is built on top of Kubernetes and is meant to modernize application development/deployment using quality engineering practices. This is done through a collection of services that can be grouped into Application Development, Application Deployment, Policy Enforcement, Service Management, Cluster Management, and Infastructure Management. 

For application development, I went with Cloud Code since that was one of the components in the Anthos Sandbox. For the most part, it's quite usefull and supports a variety of use cases.

When choosing deploying options I kinda wanted some Kuberenetes experience, so I decided not to go with Cloud Run since it does abstract away alot of the container management process. 

Policy enforcement and service management took away from the purpose of this project(also not my cup of tea), and were not feasable without actually paying for Anthos.

Now cluster management and infastructure management were intruiging especially the infastructure management part. I think cluster management is basically Kubernetes(lol and its many forms), across whatever infastructure management tool you choose to deploy on. Now what I couldn't really figure out from the documentation or the sandbox, was how to choose your infastructure management option(while trying to finesse of course). I saw some Kuberenetes cluster options while looking around Cloud Code, but everything was really ambigious which made me hesitant to experiment with cloud options($$$$). So I chose a local minikube cluster and pretended like I was one of the cool kids on the block.


### Gripes
- The deployment process is a pain. Mostly having to rebuild the container every time is really time consuming to the development process. Having some version control or only updating changes in the container would be nice
- You actually might be able to do this, but when deploying stateful applications, I would like to be able to make changes to the application without tearing down the database.
- Skaffold/Cloud Code with Kuberenetes. Cloud Code deferes alot of documentation and explanation to skaffold since that is what it is built on top of. Better documentation would be nice, especially on how to customize the deployment process, cuz I really got lost when trying to deploy this on a local/remote machine(if that makes sense). Customization seems only possible if you know what your doing, and skaffold doesn't really tell you how to integrate and fine tune your application with google services(or any other cloud provider).
- Also an editor for website previews would be nice.

### Implementation Details/Issues

Well upgrading the actual application itself was something I decided to do since I was bored, but I started to do too much(not really). 

Getting rid of celery was needed.

Now building a database for the user data also follows good engineering practices, however I tried to take it a step further. Keeping calculated data science values(PCS score) would speed up the recomendation process significantly, but it requires quite a bit of preprocessing.

To mitigate the amount of time needed for this I tried some multiprocessing. However, a progress bar was probably needed since it took about 4-5 hours total.

Here comes a sub gripe. The output Kubernetes view starts to bug out(stop emitting logs) after a certain amount of output, whether its a progress log output or streaming log output. This is not consistent with the official logs for minikube when I clicked view logs. This may not seem like a big thing, but this is little issue significantly changed the course of this application afterwards.

Anyway, I decided to create a website UI for the progress bar(now I started to do too much). This was a sub thought experiment for web app development, again cuz I was bored.

Now the problem comes in when trying to test this thing.

- VS Code Remote SSH is really nice, but for long running processes it would be nice to be able to screen the whole deployment(or something similar), close your computer, and comeback to it later in the day. Having to use workarounds like Amphetamine(lol) and ServerAliveIntervals don't really sit right with me.
- This took wayyyyy to long. Longer than when I was just outputing logs
- Now I meant to test the DB within the actual application, but the pcs calculation storage idea mmmmmm can't let that go and I didn't feel like waiting to test the whole thing. Plus there already some basic tests for the DB when loading regular data.
- This could be helped with better hardware, might try that out later
- Spell check for these README's would also be nice ( I'm not trying to look illiterate outchea)



### Conclusion (lol like this is a paper)

#### Further Implementation
- More facts about me (lmaooo)
- Apply this to different dataset (musicc????)
- Figure out how to optimize that pcs import
- Oh actually test this hoe out

This is really starting to feel like a drag, so I'm stopping for now(lol before its too late). 

