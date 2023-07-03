import logging
import os
from typing import Match, Callable 
import anyio
import openai
from semaphore import ChatContext
from semaphore.bot import Bot
from semaphore.job_queue import JobQueue
from semaphore.exceptions import StopPropagation
from semaphore.message import Message

SYSTEM_PREFIX = '📶🤖: '
CONTEXT_LIMIT = 50
MAX_TOKENS = 400

openai.api_key = os.environ.get("OPENAI_API_KEY")

logging.basicConfig(
    format='%(asctime)s %(threadName)s: [%(levelname)s] %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

class StoredChatContext(ChatContext):
    def __init__(self, message: Message, match: Match, job_queue: JobQueue, bot: Bot) -> None:
        self.all_messages: List[Message | str] = []
        super().__init__(message, match, job_queue, bot)
        # TODO metering?
        self.help_displayed = False
        self.system_prompt = "You are a helpful assistant."
        self.temperature = 0.7

    # this property is here to avoid patching the Bot class further
    # it's not clear that it expects only user messages on top, but the bot messages are the wrong class anyway
    @property
    def message(self) -> Message:
        return [m for m in self.all_messages if isinstance(m, Message)][-1]
    
    @message.setter
    def message(self, message: Message) -> None:
        self.all_messages.append(message)

class StoredContextChatBot(Bot):
    async def typing_started(self, message):
        await self._sender.typing_started(message)

    async def typing_stopped(self, message):
        await self._sender.typing_stopped(message)

    async def _handle_message(self,
                              message: Message,
                              func: Callable, match: Match) -> None:
        """Handle a matched message."""
        message_id = id(message)

        # Get context id.
        group_id: Optional[str] = message.get_group_id()
        if group_id is not None:
            context_id = f"{group_id}+{message.source.uuid}"
        else:
            context_id = message.source.uuid

        # Retrieve or create chat context.
        if self._chat_context.get(context_id, False):
            context = self._chat_context[context_id]
            context.message = message
            context.match = match
            self.log.info(f"Chat context exists for {context_id}")
        else:
            context = StoredChatContext(message, match, self._job_queue, self)
            self.log.info(f"Chat context created for {context_id}")

            # Accept group invitation.
            if group_id is not None and self._group_auto_accept:
                await self.accept_invitation(group_id)

        # Process received message and send reply.
        try:
            await func(context)
            self._chat_context[context_id] = context
            self.log.debug(f"Message ({message_id}) processed by handler {func.__name__}")
        except StopPropagation:
            raise
        except Exception as exc:
            self.log.error(
                f"Processing message ({message_id}) by {func.__name__} failed",
                exc_info=exc,
            )
            if self._exception_handler:
                await self._exception_handler(exc, context)


async def clear_context(ctx: ChatContext) -> None:
    await ctx.message.reply(body=SYSTEM_PREFIX + "Clearing chat context.")
    ctx.all_messages = []    
                            

async def display_help(ctx: ChatContext) -> None:
    message = f"""
        {SYSTEM_PREFIX} Welcome to your Signal-OpenAI chatbot relay!
        Simply begin messaging to chat, or use the following commands:
        !clear - clear the chat context (may be required if you hit the token limit)
        !prompt - set the system prompt for the model
        !temp - set the temperature for the model
        !help - display this help message

        Messages from this chatbot relay (as opposed to the LLM) are prefixed with "{SYSTEM_PREFIX}"
    """
    await ctx.message.reply(body=message)


async def set_system_prompt(ctx: ChatContext) -> None:
    system_prompt = ctx.message.get_body().replace("!prompt", "").strip()
    if system_prompt == "":
        await ctx.message.reply(body=SYSTEM_PREFIX + "Current system prompt is:\n\t" + ctx.system_prompt)
        return
    ctx.system_prompt = system_prompt
    logger.info(f'Context {ctx.message.username} reset system prompt')
    await ctx.message.reply(body=SYSTEM_PREFIX + "System prompt set to:\n\t" + system_prompt)


async def set_temperature(ctx: ChatContext) -> None:
    temperature = ctx.message.get_body().replace("!temp", "").strip()
    try:
        ctx.temperature = float(temperature)
        await ctx.message.reply(body=SYSTEM_PREFIX + "Temperature set to " + temperature)
    except ValueError:
        await ctx.message.reply(body=SYSTEM_PREFIX + "Current temperature is " + temperature)

          
async def generate_response(ctx: ChatContext) -> None:
    if not ctx.message.get_body():
        return

    prompt_messages = [{"role": "system", "content": ctx.system_prompt}]
    logger.info(f'Context {ctx.message.username} has {len(ctx.all_messages)} msg')
    if not ctx.help_displayed:
        await display_help(ctx)
        ctx.help_displayed = True
    else:
        for message in ctx.all_messages:
            # regrettably Semaphore does not represent bot replies as `Message` anywhere
            if isinstance(message, Message) and len(message.get_body()) and message.get_body()[0] != '!':
                prompt_messages.append({"role": "user", "content": message.get_body()})
            elif isinstance(message, str):
                prompt_messages.append({"role": "assistant", "content": message})

        if len(prompt_messages) > CONTEXT_LIMIT:
            await ctx.message.reply(body=SYSTEM_PREFIX + f"You reached the context maximum of {CONTEXT_LIMIT} messages. Please clear context to continue.")
        else:
            response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=prompt_messages, temperature=ctx.temperature, max_tokens=MAX_TOKENS)
            reply = response["choices"][0]["message"]["content"]
            logger.info(f'{response["usage"]["completion_tokens"]} tokens') 
            await ctx.message.reply(body=reply)
            ctx.all_messages.append(reply)
 
async def main() -> None:
    """Start the bot."""
    # Connect the bot to number.
    async with StoredContextChatBot(os.environ["SIGNAL_PHONE_NUMBER"], profile_name="Signal-OpenAI Relay") as bot:
        # TODO global exception handlers?
        bot.register_handler("!clear", clear_context)
        bot.register_handler("!help", display_help)
        bot.register_handler("!prompt", set_system_prompt)
        bot.register_handler("!temp", set_temperature)
        bot.register_handler("^(?!!).*", generate_response)

        # Run the bot until you press Ctrl-C.
        await bot.start()


if __name__ == '__main__':
    anyio.run(main)
