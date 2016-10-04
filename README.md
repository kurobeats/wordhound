# README #

Wordhound

This is a tool that allows for the automated and targeted construction of wordlists and dictionaries for use in conjunction with password attacks.

It builds dictionaries off of generic websites, plain text (for example emails), Twitter, PDF's and Reddit.

### How do I get set up? ###

Run 

python setup.py install && ./setup.sh

Edit wordhound.conf.dist and input the relevant information such as your twitter api key if you want to use twitter. Save this file as wordhound.conf.

Twitter

Setup your twitter api and edit the wordhound.conf file with your new keys

Threshold

You can adjust the threshold value in the wordhound.conf file to either filter more or less results.

### The mechanics, motivation and idea behind wordhound ###

People can't generate randomness. Their passwords are influenced by who they are. Creating a dictionary that contains information around any of the attributes that make them up is a good starting point for attacking passwords that are not tackled using basic methods and common password lists.

For a more interesting discussion around this:
http://www.irongeek.com/i.php?page=videos/passwordscon2014/target-specific-automated-dictionary-generation-matt-marx

@tehnlulz
