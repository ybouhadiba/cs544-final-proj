## Python QUIC Shell

1. Install dependencies with pip (requirements.txt) is provided
2. The certs in the ./certs directory are fine for testing there is a script if you want to rebuild your own but you will need openssl installed
3. run `python3 echo.py server` to start the server with defaults and `python3 echo.py client` to start the client with defaults.
4. Refer to users.json for user login info.

Correct output for server:

```sh
(.venv) ➜  python git:(main) ✗ python3 echo.py server
[svr] Server starting...
[svr] received message:  This is a test message
```

Correct output for client:


```sh
(.venv) ➜  python git:(main) ✗ python3 echo.py client
[cli] starting client
Please log in to an account.
Username: BigMode
Password: yes
Successful login. Currently online users: BigMode
Type /exit to log out.
[cli] starting receive_messages
BigMode has joined the chat.
```