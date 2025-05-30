# SuperMarketApp

# Contents:
- [Beginner Guide](#beginner-guide)
- [Jinja Syntax for Beginners] (#jinja-syntax)
- [Project Schema] (#project-schema)
- [HTML Beginning] (#html-beginning)
## Beginner Guide
## Read me syntax
You can use the following [link](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax) to see the README.md syntax.
## Beginner Guide to Git
### How to add branch on git
```
git checkout -b <branch-name>
git push origin <branch-name>
```
### If you do not have remote origin you can add it as follow:
```
git remote add origin <ssh-link>
```
## Jinja Syntax
### How to extend a page
```
{% extends "layout/default.html" %}
```
This will use the default.html as the base page and put everything on top of it in the designated places
### How to indicate place
```
<title>{%block title%}{%endblock%}</title>
```
So what this does is indicate this place is going to be used for title and you can change the title in each pages using only the following after you extend from the page as follow:
```
<title>{%block title%}Hello{%endblock%}</title>
```
So the title for the extended page is now Hello.
## How to add elements based on the return type
Since we are going to return some queries, some items to the page on the backend, in the frontend we need to use the following jinja syntax:
```
<ul>
{% for item in seq %}
    <li>{{ item }}</li>
{% endfor %}
</ul>
```
Which is actually the **for loop** as it could be easily seen. What it does is, it takes the items based on the return type and then list the items in seq. You can think of **{{item}}** as like variable. This is used to indicate variables on jinja. 
Variables are actually pretty much important, since I can send the variable to the page on flask and the jinja will use this variable and place the variable to its place. It is pretty important and usefull tool.
Even though this would be enough for now, for more information you can read look to [this link](https://jinja.palletsprojects.com/en/stable/templates/) for more information.

## Project Schema
Since we are using Flask to create this project, there needs to be some changes in the structure of the app. I have decided to do the following structure for the app for it to be more suitable to flask:
```
supermarketApp/
├── app/
│   ├── app.py
│   ├── dbHandler.py
│   └── templates/
│   |   ├── index.html
│   |   ├── login.html
│   |   └── ...
│   └── static/
│   |   ├── css
|   |   | └── main.ss 
│   |   ├── js
│   |   └── ...
├── images/
├── styles/
├── README.md
└── ...
```

We are going to use the **template** folder inside the **app** folder to put our **HTML files**. It is actually pretty important since otherwise, the app will not realize our HTML files and will not render as it should. It also brings structure to our app so it would be great to use it for this reason as well.

Although with this change, there could be some problems since the app links now need to change when they have added. 

### How to add links now
Since now we are using Flask, we cannot use the following:
```
<li><a href="login.html">Login</a></li>
```
What we now need to use is:
```
<li><a href="{{ url_for('login') }}">Home</a></li>
```

As you couls see the only change is instead of using **href="login.html"** we are using **href="{{ url_for('login') }}**. It is not a big change although be carefull since this will impact the app throughly. If you recieve an error that says **Not Found** then you are probably using **href="login.html"** instead of **href="{{ url_for('login') }}**. Keep this in mind

## HTML Beggining

We are now also using Jinja for simplicty. It would be a waste of time and resources to copy paste the navigation bar -which used in nearly every pages- so instead now, we are going to use Jinja. 

You do not need to know the whole jinja, just look at the ones in [here] (#jinja-syntax) if you are feeling out of blue, that would be enough.

Every page in our template folder is going to beggin as follows:
```
{%extends 'base.html'%}
{%block title%}Your Title{%endblock%}
{%block content%}
    Add your content in here
{%endblock%}
```
You can simply copy paste the above code and add the new content in between the content block. 

