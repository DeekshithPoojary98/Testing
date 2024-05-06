*** Settings ***
Library 	Selenium2Library

*** Test Cases ***
TC1
	Open browser	https://google.com
	Wait until element is visible	//textarea[@name='q']
	Input Text	//textarea[@name='q']	Google
	Press key	None	ENTER
	Close browser

