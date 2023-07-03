import os
from typing import Match
import anyio
import openai
import semaphore
from semaphore import ChatContext
from semaphore.bot import Bot
from semaphore.job_queue import JobQueue
from semaphore.message import Message

SYSTEM_PREFIX = '📶🤖: '

openai.api_key = os.environ.get("OPENAI_API_KEY")

class StoredChatContext(ChatContext):
    def __init__(self, message: Message, match: Match, job_queue: JobQueue, bot: Bot) -> None:
        super().__init__(message, match, job_queue, bot)
        # limits to chat context?
        self.all_messages = []
        self.system_prompt = "You are a helpful assistant."
        self.temperature = 0.7

    @property
    def message(self) -> semaphore.Message:
        return self.all_messages[-1]
    
    @message.setter
    def message(self, message: semaphore.Message) -> None:
        self.all_messages.append(message)

ChatContext = StoredChatContext

async def clear_context(ctx: ChatContext) -> None:
    ctx.all_messages = []    
    await ctx.message.reply(body=SYSTEM_PREFIX + "Chat context cleared.")
                            

async def display_help(ctx: ChatContext) -> None:
    ctx.all_messages = []
    message = """
        {SYSTEM_PREFIX} Welcome to your Signal-OpenAI chatbot relay!
        Simply begin messaging to chat, or use the following commands:
        !clear - clear the chat context (may be required if you hit the token limit)
        !prompt - set the system prompt for the model
        !temp - set the temperature for the model
        !help - display this help message

        Messages from this chatbot relay (as opposed to the LLM) are prefixed with {SYSTEM_PREFIX}.
    """
    await ctx.message.reply(body=message)


async def set_system_prompt(ctx: ChatContext) -> None:
    system_prompt = ctx.message.get_body().replace("!prompt ", "").strip()
    if system_prompt == "":
        await ctx.message.reply(body=SYSTEM_PREFIX + "Current system prompt is:\n\t" + ctx.system_prompt)
        return
    ctx.system_prompt = system_prompt
    await ctx.message.reply(body=SYSTEM_PREFIX + "System prompt set to:\n\t" + system_prompt)


async def set_temperature(ctx: ChatContext) -> None:
    temperature = ctx.message.get_body().replace("!temp ", "")
    try:
        ctx.temperature = float(temperature)
        await ctx.message.reply(body=SYSTEM_PREFIX + "Temperature set to " + temperature)
    except ValueError:
        await ctx.message.reply(body=SYSTEM_PREFIX + "Current temperature is " + temperature)

          
async def generate_response(ctx: ChatContext) -> None:
    prompt_messages = [{"role": "system", "content": ctx.system_prompt}]
    for message in ctx.all_messages:
        if message.username == ctx.bot.username:
            prompt_messages.append({"role": "assistant", "content": message.get_body()})
        else:
            prompt_messages.append({"role": "user", "content": message.get_body()})
    openai.ChatCompletion.create(model="gpt-3.5-turbo", prompt=prompt_messages, temperature=ctx.temperature)

async def main() -> None:
    """Start the bot."""
    # Connect the bot to number.
    async with semaphore.Bot(os.environ["SIGNAL_PHONE_NUMBER"]) as bot:
        # TODO global exception handlers?
        bot.register_handler("!clear", clear_context)
        bot.register_handler("!help", display_help)
        bot.register_handler("!prompt", set_system_prompt)
        bot.register_handler("!temp", set_temperature)
        bot.register_handler("", generate_response)

        # Run the bot until you press Ctrl-C.
        await bot.start()


if __name__ == '__main__':
    anyio.run(main)