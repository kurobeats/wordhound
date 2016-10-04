from setuptools import setup

setup(name="WordHound",
	version = '0.1',
	description = "Automated dictionary generation",
	author = "tehnlulz",
	author_email = "matthewdmarx@gmail.com",
	license = 'MIT',
	install_requires = ['requests','nltk', 'numpy', 'tweepy', 'beautifulsoup'],
	dependency_links = ['http://www.crummy.com/software/BeautifulSoup/bs4/download/4.3/beautifulsoup4-4.3.2.tar.gz'],
	zip_safe = False
	)
