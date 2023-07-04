The **Signal-ChatGPT Relay** makes an OpenAI chatbot available over Signal messenger.

This may be useful to those who need AI on an airplane, as some airliners provide free messaging service for Signal. It may also be useful in jurisdictions where ChatGPT is not available. Some extra control of the model, such as modifying the system prompt, is also provided.

## Active Instance

[+1 775-235-2686](tel:+17752352686) 

## Dependencies and installation instructions

You can run your own or modify this bot with a Signal number you control. You should register the number on a phone (perhaps with a Google Voice number), and then link it with the `signaldctl link` command as shown below. Don't bother trying to register a new number with `signald` due to CAPTCHA. 

### System dependencies
* Linux (until Dockerized)
* signald (https://signald.org/articles/install/)
* Python 3

1. Link your Signal number to signald.
```

```
2. Clone the repo and install dependencies inside a venv
```

```
3. Edit the paths in `signal-chatgpt.service` to match the clone dir and venv dir, and fill in the 2 environment variables.
4. Copy the service file, load and enable
5. View logs



