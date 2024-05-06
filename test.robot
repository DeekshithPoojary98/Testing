*** Settings ***
Library 	Selenium2Library

*** Test Cases ***
TC1
	Open browser	https://google.com	headlesschrome
	Wait until element is visible	//textarea[@name='q']
	Input Text	//textarea[@name='q']	Google
	Press key	//textarea[@name='q']	ENTER
	Close browser

