# ludopedia_wrapper

A simple python wrapper for ludopedia's API
https://ludopedia.com.br/api/documentacao.html


To use this wrapper it is necessary to create an application at ludopedia 
https://www.ludopedia.com.br/aplicativos

Once it is created, it is necessary to create a json config file like the example below:
```
{
    "APP_ID": <APP_ID>,
    "APP_KEY": <APP_KEY>,
    "ACESS_TOKEN": <ACESS_TOKEN>,
    "CODE_URL":"http://localhost:5000"
}
```
This CODE_URL is the address your application is running. The reason it is needed is because ludopedia needs you to login in their website (when calling method connect from an instance of a Connection object the website should be open). Once authenticated at ludopedia the module should get a code and automatically request a token to the server. This token is a default oauth2 code valid for 60 days. Once you get this token, it should be saved by the module and then not needed anymore. So it won´t be necessary to run this connect method until your token become invalid

Added suport do .env file using Decouple  
The .env file should provide path to json mentioned above.