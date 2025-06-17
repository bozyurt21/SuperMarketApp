# SuperMarketApp

# Contents:


- [Beginner Guide](#beginner-guide)
- [How to Import/ Export db](#how-to-import-export-db)
- [How To Run The App](#how-to-run-the-app)
- [Jinja Syntax for Beginners](#jinja-syntax)
- [HTML Beginning](#html-beginning)

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

## How to Import/ Export db

# Export DB
```
mysqldump -u user_name -p db_name > path/to/file_name.sql
```

# Import DB
```
mysql -u user_name -p db_name < path/to/file_name.sql
```
## How To Run The App

```
python3 app/app.py
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

## HTML Beginning

```
{%extends 'base.html'%} {%block title%}Home{%endblock%} {%block
content%}{%endblock%}
```
