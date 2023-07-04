![image](https://github.com/dillonwilliams/signal-chatgpt/assets/1835005/e5e5aa18-4d5e-49ed-8650-785a4c3ab3a4)


The Signal-ChatGPT Relay makes an OpenAI chatbot available over Signal messenger.

This is good for those who need AI on an airplane, as some airliners provide free messaging service for Signal. It may also be useful in jurisdictions where ChatGPT is not available. Some extra control of the model such as modifying the system prompt is also provided.

## Active instance
Message __+1 775-235-2686__ on Signal, or add it to your contacts with [this link](vcard.vcf?raw=1) or the QR code below. 

<img width="100" alt="vcard2" src="https://github.com/dillonwilliams/signal-chatgpt/assets/1835005/e72b8a18-73e0-4576-873f-678334cc6308">


## Dependencies and installation instructions
This mostly uses the [Semaphore](https://github.com/lwesterhof/semaphore) library for Signal functionality. 

You can run your own or modify this bot with a Signal number you control. You should register the number on a phone (perhaps with a Google Voice number), and then link it with the `signaldctl account link` command as shown below. Don't bother trying to register a new number with `signald`, as it doesn't work with the new CAPTCHA. 

### System dependencies
* Linux (until Dockerized)
* signald (https://signald.org/articles/install/)
* Python 3 w/ pip and virtualenv suport

### Steps
1. Link your Signal number to signald.
```
signaldctl account link +XXXXXXXXXXX
# a QR code appears on screen that you scan with your phone
```
2. Clone the repo and install dependencies inside a venv
```
git clone git@github.com:dillonwilliams/signal-chatgpt.git
python -m venv venv
source venv/bin/activate
cd signal-chatgpt
pip install -r requirements.txt
```
3. Edit the paths in `signal-chatgpt.service` to match the clone dir and venv dir, and fill in the 2 environment variables.
4. Copy the service file, load and enable
```
sudo cp signal-chatgpt.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable signal-chatgpt
sudo systemctl start signal-chatgpt
```
6. View logs with `sudo journalctl -u signal-chatgpt`

For dev work, simply run `python bot.py` inside your virtualenv.


