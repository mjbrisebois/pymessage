from setuptools import setup

setup(
    name			= "pymessage",
    packages			= [
        "pymessage",
        "pymessage/utils",
    ],
    package_dir			= {
        "pymessage":		".", 
        "pymessage/utils":	"./utils", 
    },
    version			= "0.1.3",
    description			= "Python library for reading and managing Apple iMessage database",
    author			= "Matthew Brisebois",
    author_email		= "matthew@webheroes.ca",
    url				= "https://github.com/mjbrisebois/pymessage",
    keywords			= ["pymessage", "imessage"],
    classifiers			= [],
)
